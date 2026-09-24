"""
python manage.py import_new_articles --file /path/to/your/data.xlsx(带引号) --format excel
"""

from django.core.management.base import BaseCommand
import pandas as pd
from articles.models import Article, Category
from django.core.files import File
from pathlib import Path
import os

class Command(BaseCommand):
    help = '从自定义数据源导入文献'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='数据文件路径')
        parser.add_argument('--format', type=str, default='excel', help='数据格式(excel/csv)')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file']
        data_format = kwargs['format']
        
        if not file_path or not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'文件不存在: {file_path}'))
            return
            
        # 读取数据
        if data_format == 'excel':
            df = pd.read_excel(file_path)
        elif data_format == 'csv':
            df = pd.read_csv(file_path)
        else:
            self.stdout.write(self.style.ERROR(f'不支持的数据格式: {data_format}'))
            return
            
        # 获取或创建默认分类
        default_category, _ = Category.objects.get_or_create(name='未分类')
        
        # 导入数据
        for _, row in df.iterrows():
            try:
                # 处理分类信息
                category = default_category
                if 'category' in row and row['category']:
                    # 如果数据中有分类字段，则使用该分类
                    category_name = row['category']
                    category, _ = Category.objects.get_or_create(name=category_name)
                    self.stdout.write(self.style.SUCCESS(f'使用分类: {category_name}'))
                
                # 创建文章记录
                article = Article(
                    title=row.get('title', '无标题'),
                    author=row.get('author', 'Unknown'),
                    abstract=row.get('abstract', ''),
                    content=row.get('content', ''),
                    source=row.get('source', 'Unknown'),
                    source_type=row.get('source_type', '期刊'),
                    keywords=row.get('keywords', ''),
                    category=category  # 使用获取到的分类
                )
                
                # 保存文章
                article.save()
                
                # 如果有PDF文件路径，添加文件
                pdf_path = row.get('pdf_path')
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as f:
                        file_name = os.path.basename(pdf_path)
                        article.file_path.save(file_name, File(f), save=True)
                
                self.stdout.write(self.style.SUCCESS(f'成功导入文章: {article.title}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'导入失败: {row.get("title", "未知")} - {str(e)}'))



