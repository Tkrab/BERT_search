import os
import re

def rename_files():
    folder_path = 'data/paper'
    
    # 确保文件夹存在
    if not os.path.exists(folder_path):
        print(f"文件夹 {folder_path} 不存在")
        return
    
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 使用正则表达式匹配文件名模式
        match = re.match(r'(.*?)_[a-zA-Z0-9]{7}(\.[^.]+)$', filename)
        if match:
            # 构建新的文件名
            new_filename = match.group(1) + match.group(2)
            
            # 构建完整的文件路径
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_filename)
            
            # 重命名文件
            try:
                os.rename(old_path, new_path)
                print(f'已重命名: {filename} -> {new_filename}')
            except Exception as e:
                print(f'重命名 {filename} 时出错: {str(e)}')

if __name__ == '__main__':
    rename_files()