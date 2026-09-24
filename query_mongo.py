from transformers import BertTokenizer, BertModel
import torch
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass
from pymongo import MongoClient

# MongoDB 配置
MONGO_USER = 'vector_admin'
MONGO_PASSWORD = 'vector_admin'
MONGO_DB = 'vector_db_v5'
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_URI = f'mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}'

@dataclass
class ChunkInfo:
    """用于存储文档块信息的数据类"""
    doc_id: str          # 文档标识符（文件名）
    chunk_id: int        # 块的序号
    text: str           # 块的文本内容
    start_pos: int      # 在原文中的起始位置
    end_pos: int        # 在原文中的结束位置

@dataclass
class SearchResult:
    """搜索结果数据类"""
    doc_id: str
    chunk_id: int
    text: str
    distance: float

class BertSearch:
    def __init__(self, model_name: str = "bert-base-uncased"):
        # 初始化BERT tokenizer和模型
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # 连接MongoDB
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.chunks_collection = self.db['chunks']

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

    def search_similar(self, query: str, batch_size: int = 1000, top_k: int = 5) -> List[SearchResult]:
        """检索方法"""
        query_vector = self.encode_text(query)
        query_vector = query_vector / np.linalg.norm(query_vector)
        
        all_results = []
        total_docs = self.chunks_collection.count_documents({})
        
        for skip in range(0, total_docs, batch_size):
            batch_docs = list(self.chunks_collection.find({}).skip(skip).limit(batch_size))
            
            if not batch_docs:
                break
                
            batch_chunks = []
            batch_vectors = []
            
            for doc in batch_docs:
                batch_chunks.append({
                    'doc_id': doc['doc_id'],
                    'chunk_id': doc['chunk_id'],
                    'text': doc['text']
                })
                vector = np.frombuffer(doc['vector'], dtype=np.float32)
                vector = vector / np.linalg.norm(vector)
                batch_vectors.append(vector)
            
            # 计算相似度
            batch_vectors = np.array(batch_vectors)
            similarities = np.dot(batch_vectors, query_vector)
            
            # 上下文加权
            weighted_similarities = similarities.copy()
            for i in range(1, len(similarities)):
                weighted_similarities[i] += similarities[i-1] * 0.15
            for i in range(len(similarities)-1):
                weighted_similarities[i] += similarities[i+1] * 0.15
            
            # 关键词匹配权重
            query_terms = set(query.lower().split())
            for i, chunk in enumerate(batch_chunks):
                text_terms = set(chunk['text'].lower().split())
                term_overlap = len(query_terms & text_terms) / len(query_terms)
                weighted_similarities[i] += term_overlap * 0.3
            
            # 转换为距离值（1 - 相似度）使其与 Milvus 的距离概念一致
            distances = 1 - weighted_similarities
            
            batch_results = [
                SearchResult(
                    doc_id=chunk['doc_id'],
                    chunk_id=chunk['chunk_id'],
                    text=chunk['text'],
                    distance=float(dist)
                )
                for chunk, dist in zip(batch_chunks, distances)
            ]
            all_results.extend(batch_results)
            
            del batch_chunks
            del batch_vectors
        
        all_results.sort(key=lambda x: x.distance)  # 按距离升序排序
        return all_results[:top_k]

def timmer(func):
    def wrapper():
        import time
        start_time = time.time()
        func()
        end_time = time.time()
        print(f"耗时: {end_time - start_time}秒")
    return wrapper

@timmer
def main():
    searcher = BertSearch()
    
    try:
        query = "decision-maker perspectives regarding"
        print(f'执行查询: {query}')
        
        results = searcher.search_similar(
            query=query,
            batch_size=1000,
            top_k=5
        )

        print(f"\n找到 {len(results)} 条相关结果:")
        for result in results:
            print(f"\n文档: {result.doc_id}")
            print(f"块ID: {result.chunk_id}")
            print(f"相似度得分: {1 - result.distance:.4f}")  # 转换回相似度显示
            print(f"文本: {result.text}")
            print("-" * 80)
            
    except Exception as e:
        print(f"错误: {str(e)}")
        raise

def timmer(func):
    def wrapper():
        import time
        start_time = time.time()
        func()
        end_time = time.time()
        print(f"耗时: {end_time - start_time}秒")

    return wrapper
        

if __name__ == "__main__":
    main()
