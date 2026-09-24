from rest_framework import serializers
from .models import Article, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ArticleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'author', 'abstract', 'source', 'source_type', 
                 'created_at', 'citation_count', 'views', 'category_name']

    def get_matched_texts(self, obj):
        matches = getattr(obj, 'matched_texts', [])
        return [{'text': match['text']} for match in matches]