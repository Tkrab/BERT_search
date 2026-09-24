from django.core.management.base import BaseCommand
from django.db.models import Count
from articles.models import Article, HotArticle, UserSearchHistory
from query_mongo import BertSearch
from django.utils import timezone

class Command(BaseCommand):
    help = '更新热门文章列表'

    def handle(self, *args, **kwargs):
        try:
            # 获取最近的热门搜索词
            hot_searches = UserSearchHistory.objects.values('search_query').annotate(
                search_count=Count('search_query')
            ).order_by('-search_count', '-search_time')[:10]

            # 初始化 MilvusQuery
            # milvus_query = MilvusQuery()
            # 初始化 BertSearch
            bert_search = BertSearch()
            
            article_scores = {}
            
            # 对每个热门搜索词进行向量搜索
            for hot_search in hot_searches:
                try:
                    # similar_results = milvus_query.search_similar(
                    #     hot_search['search_query'],
                    #     top_k=10
                    # )
                    similar_results = bert_search.search_similar(
                        hot_search['search_query'],
                        top_k=10
                    )
                    
                    # 累计文章得分
                    for result in similar_results:
                        article = Article.objects.filter(
                            file_path__icontains=result.doc_id
                        ).first()
                        if article:
                            score = 1 - result.distance
                            if article.id in article_scores:
                                article_scores[article.id]['score'] += score * hot_search['search_count']
                            else:
                                article_scores[article.id] = {
                                    'article': article,
                                    'score': score * hot_search['search_count']
                                }
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'处理热门搜索词时出错: {str(e)}'))
                    continue

            # 清除旧的热门文章
            HotArticle.objects.all().delete()
            
            # 保存新的热门文章
            if article_scores:
                sorted_articles = sorted(
                    article_scores.items(),
                    key=lambda x: x[1]['score'],
                    reverse=True
                )[:10]
                
                for rank, (article_id, data) in enumerate(sorted_articles, 1):
                    HotArticle.objects.create(
                        article=data['article'],
                        score=data['score'],
                        rank=rank,
                        updated_at=timezone.now()
                    )
            else:
                # 如果没有基于搜索的热门文章，使用访问量最高的文章
                for rank, article in enumerate(Article.objects.order_by('-views')[:10], 1):
                    HotArticle.objects.create(
                        article=article,
                        score=float(article.views),
                        rank=rank,
                        updated_at=timezone.now()
                    )

            self.stdout.write(self.style.SUCCESS('成功更新热门文章列表'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'更新热门文章失败: {str(e)}'))