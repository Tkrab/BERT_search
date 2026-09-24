import sqlite3
import re

def update_file_paths():
    # 连接到数据库
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # 获取所有文章记录
    cursor.execute('SELECT id, file_path FROM articles')
    articles = cursor.fetchall()

    # 更新每条记录
    for article_id, file_path in articles:
        if file_path:
            # 使用正则表达式匹配并替换文件名中的随机字符串后缀
            new_path = re.sub(r'(.*?)_[a-zA-Z0-9]{7,8}(\.pdf)$', r'\1\2', file_path)
            
            # 如果路径发生了变化，则更新数据库
            if new_path != file_path:
                cursor.execute('UPDATE articles SET file_path = ? WHERE id = ?', 
                             (new_path, article_id))
                print(f'Updated: {file_path} -> {new_path}')

    # 提交更改并关闭连接
    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_file_paths()