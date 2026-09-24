from django.core.management.base import BaseCommand
from articles.models import Article, Category
import random
"""
class Command(BaseCommand):
    help = '创建文献分类, 随机分配文章'

    def handle(self, *args, **kwargs):
        # 创建分类
        categories = [
            '海运经济与金融',
            '港口物流管理',
            '航运市场分析',
            '海事法律研究',
            '智慧航运技术',
            '船舶工程技术',
            '航运安全管理',
            '港口规划建设',
            '国际航运政策',
            '绿色航运发展'
        ]
        
        # 创建分类记录
        created_categories = []
        for cat_name in categories:
            category, created = Category.objects.get_or_create(name=cat_name)
            created_categories.append(category)
            status = '创建' if created else '已存在'
            self.stdout.write(self.style.SUCCESS(f'{status}分类: {cat_name}'))
            
        # 文章随机分配分类
        articles = Article.objects.all()
        for article in articles:
            article.category = random.choice(created_categories)
            article.save()
            self.stdout.write(self.style.SUCCESS(f'文章 "{article.title}" 已分配到分类 "{article.category.name}"'))
"""