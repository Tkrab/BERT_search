import os
import re
import numpy as np
import torch
from transformers import BertTokenizer, BertModel
from pymongo import MongoClient
from tqdm import tqdm
from dataclasses import dataclass


# 文献TXT文件目录
paper_txt_dir = "/path/to/paper_txt"

# MongoDB 配置
MONGO_USER = 'vector_admin'
MONGO_PASSWORD = 'vector_admin'
MONGO_DB = 'vector_db_v5'
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_URI = f'mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}'

# 文本块大小配置
CHUNK_SIZE = 500  # 每个文本块的大小（字符数）
OVERLAP = 100     # 块之间的重叠部分（字符数）


@dataclass
class ChunkInfo:
    """用于存储文档块信息的数据类"""
    doc_id: str          # 文档标识符（文件名）
    chunk_id: int        # 块的序号
    text: str            # 块的文本内容
    start_pos: int       # 在原文中的起始位置
    end_pos: int         # 在原文中的结束位置

class VectorUpdater:
    def __init__(self, model_name: str = "bert-base-uncased"):
        # 初始化BERT tokenizer和模型
        print("正在加载BERT模型...")
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"使用设备: {self.device}")
        self.model.to(self.device)
        
        # 连接MongoDB
        print("正在连接MongoDB...")
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.chunks_collection = self.db['chunks']
        print("MongoDB连接成功")

    def encode_text(self, text: str) -> np.ndarray:
        """文本编码方法"""
        inputs = self.tokenizer(
            text, 
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            
        # 使用最后4层的平均表示
        last_four_layers = outputs.hidden_states[-4:]
        last_hidden_states = torch.stack(last_four_layers).mean(0)
        
        attention_mask = inputs['attention_mask']
        masked_hidden_states = last_hidden_states * attention_mask.unsqueeze(-1)
        sum_hidden_states = torch.sum(masked_hidden_states, dim=1)
        count_non_masked = torch.sum(attention_mask, dim=1, keepdim=True)
        mean_pooled = sum_hidden_states / count_non_masked
        
        vector = mean_pooled.cpu().numpy()[0]
        return vector / np.linalg.norm(vector)

    def chunk_document(self, doc_id: str, text: str) -> list:
        """将文档分割成块"""
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            
            # 如果不是最后一块，尝试在空格或换行处截断
            if end < len(text):
                # 在CHUNK_SIZE范围内找最后一个换行符
                last_newline = text.rfind('\n', start, end)
                if last_newline > start + CHUNK_SIZE // 2:
                    end = last_newline + 1
                else:
                    # 如果没有合适的换行符，找最后一个空格
                    last_space = text.rfind(' ', start, end)
                    if last_space > start + CHUNK_SIZE // 2:
                        end = last_space + 1
            
            chunk_text = text[start:end].strip()
            if chunk_text:  # 确保块不为空
                chunks.append(ChunkInfo(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    text=chunk_text,
                    start_pos=start,
                    end_pos=end
                ))
                chunk_id += 1
            
            # 移动到下一个块的起始位置，考虑重叠
            start = end - OVERLAP if end < len(text) else len(text)
        
        return chunks

    def process_file(self, file_path: str) -> None:
        """处理单个文件，提取文本块并更新到数据库"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用文件名作为文档ID
            doc_id = os.path.basename(file_path)
            
            # 检查数据库中是否已存在该文档
            existing_count = self.chunks_collection.count_documents({"doc_id": doc_id})
            if existing_count > 0:
                print(f"文档 {doc_id} 已存在于数据库中，跳过处理")
                return
            
            # 分块处理文档
            chunks = self.chunk_document(doc_id, content)
            print(f"文档 {doc_id} 被分割为 {len(chunks)} 个块")
            
            # 为每个块生成向量并存储到数据库
            for chunk in chunks:
                vector = self.encode_text(chunk.text)
                
                # 将向量转换为二进制格式存储
                vector_binary = vector.astype(np.float32).tobytes()
                
                # 存储到MongoDB
                self.chunks_collection.insert_one({
                    "doc_id": chunk.doc_id,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "start_pos": chunk.start_pos,
                    "end_pos": chunk.end_pos,
                    "vector": vector_binary
                })
            
            print(f"文档 {doc_id} 处理完成并存储到数据库")
        
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {str(e)}")

    def update_all_documents(self, directory: str) -> None:
        """处理目录中的所有TXT文件并更新到数据库"""
        if not os.path.exists(directory):
            print(f"目录 {directory} 不存在")
            return
        
        # 获取所有TXT文件
        txt_files = [os.path.join(directory, f) for f in os.listdir(directory) 
                    if f.endswith('.txt') and os.path.isfile(os.path.join(directory, f))]
        
        if not txt_files:
            print(f"目录 {directory} 中没有找到TXT文件")
            return
        
        print(f"找到 {len(txt_files)} 个TXT文件待处理")
        
        # 使用tqdm显示进度
        for file_path in tqdm(txt_files, desc="处理文件"):
            self.process_file(file_path)
        
        print("所有文件处理完成")

def main():
    
    # 创建更新器并处理所有文档
    updater = VectorUpdater()
    updater.update_all_documents(paper_txt_dir)

if __name__ == "__main__":
    main()