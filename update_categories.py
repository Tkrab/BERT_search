import os
import django
import re
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'literature_system.settings')
django.setup()

from articles.models import Category, Article
from django.db import transaction

def parse_clustering_results():
    new_categories = []
    cluster_files = {}
    current_cluster = None
    
    with open('clustering_results.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        category_match = re.match(r'(.*?) \(聚类 (\d+)\):', line)
        if category_match:
            category_name = category_match.group(1)
            cluster_id = int(category_match.group(2))
            new_categories.append(category_name)
            current_cluster = cluster_id
            cluster_files[current_cluster] = []
            continue
            
        if line.startswith('- '):
            filename = line[2:].replace('.txt', '')  
            if current_cluster is not None:
                cluster_files[current_cluster].append(filename)
                
    return new_categories, cluster_files

def update_categories_and_articles():
    try:
        # 从聚类结果文件中读取分类和文件信息
        new_categories, cluster_files = parse_clustering_results()
        
        with transaction.atomic():
            # 更新分类
            categories = {}
            for i, name in enumerate(new_categories):
                category, created = Category.objects.get_or_create(name=name)
                categories[i] = category
                if created:
                    print(f"创建新分类: {name}")
                else:
                    print(f"使用现有分类: {name}")
            
            # 更新文章表
            for cluster_id, files in cluster_files.items():
                category = categories[cluster_id]
                print(f"\n正在处理分类 '{category.name}':")
                
                for filename in files:
                    file_path = f"paper/{filename}"
                    try:
                        article = Article.objects.get(file_path=file_path)
                        article.category = category
                        article.save()
                        print(f"更新文章分类: {file_path}")
                    except Article.DoesNotExist:
                        print(f"文章未找到: {file_path}")
            
            print("\n分类更新完成！")
            
    except Exception as e:
        print(f"更新过程中出现错误: {str(e)}")

if __name__ == "__main__":
    # print(parse_clustering_results())
    update_categories_and_articles()
