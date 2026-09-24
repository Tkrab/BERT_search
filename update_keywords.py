import pandas as pd
import re
from sqlalchemy import create_engine, text
import os

# 读取Excel文件
df = pd.read_excel('data/article_data.xlsx')

# 创建数据库连接
engine = create_engine('sqlite:///db.sqlite3')

def process_keywords(keywords_str):
    # 移除 "Keywords:" 前缀（如果存在）
    keywords_str = re.sub(r'^.*Keywords:', '', keywords_str).strip()
    
    # 通过大写字母分割字符串，但保留分割后的大写字母
    words = re.findall('[A-Z][^A-Z]*', keywords_str)
    
    # 过滤掉可能的分类代码（如C70、R41等）
    keywords = [word.strip() for word in words if not re.match(r'^[A-Z][0-9]+$', word.strip())]
    
    return ','.join(keywords)

def update_database():
    with engine.connect() as conn:
        for _, row in df.iterrows():
            file_name = row['file_name']
            keywords = row['keywords']
            
            if pd.isna(keywords):
                continue
                
            # 构建file_path
            file_path = f"paper/{file_name}"
            
            # 处理keywords
            processed_keywords = process_keywords(keywords)
            
            # 更新数据库
            update_query = text("""
                UPDATE articles 
                SET keywords = :keywords 
                WHERE file_path = :file_path
            """)
            
            conn.execute(update_query, {
                'keywords': processed_keywords,
                'file_path': file_path
            })
            conn.commit()

if __name__ == "__main__":
    update_database()
    print("Keywords update completed!")