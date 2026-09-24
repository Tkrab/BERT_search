from django.db import models
from django.conf import settings
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'categories'

class Article(models.Model):
    title = models.CharField(max_length=200)
    abstract = models.TextField(blank=True, default='')
    content = models.TextField(blank=True, default='')
    author = models.CharField(max_length=100, default='Unknown')
    source = models.CharField(max_length=100, default='Unknown')
    source_type = models.CharField(max_length=50, default='期刊')
    publication_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.IntegerField(default=0)
    citation_count = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    
    file_path = models.FileField(
        upload_to='paper/',
        null=True,
        blank=True,
        verbose_name='文献文件'
    )
    
    def __str__(self):
        return self.title
    keywords = models.CharField(max_length=500, blank=True, null=True, help_text='文章关键词，多个关键词用逗号分隔')

    class Meta:
        db_table = 'articles'
        ordering = ['-created_at']

class Collection(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='collections')
    article = models.ForeignKey('Article', on_delete=models.CASCADE, related_name='collected_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'article')
        db_table = 'collections'

class UserSearchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    search_query = models.CharField(max_length=255)
    search_time = models.DateTimeField(auto_now_add=True)
    vector_embedding = models.JSONField(null=True, blank=True)  # 存储搜索词的向量嵌入

    class Meta:
        ordering = ['-search_time']
        db_table = 'user_search_history'

class HotArticle(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE)
    score = models.FloatField()
    rank = models.IntegerField()
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['rank']
