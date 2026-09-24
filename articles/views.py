from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q  # 添加 Count 导入
from .models import Article, Category, HotArticle
from .serializers import ArticleSerializer, CategorySerializer
from rest_framework.pagination import PageNumberPagination
from django.http import HttpResponse
from django.http import FileResponse
from django.utils.http import quote
import os
from .models import Collection
# from query_milvus import MilvusQuery 
from query_mongo import BertSearch
from .models import UserSearchHistory


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action == 'collect':
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=False, methods=['get'])
    def search_ori(self, request):
        
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        source_type = request.query_params.get('source_type', '')
        sort = request.query_params.get('sort', 'relevance')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        # 添加认证信息调试
        print(f"Authorization header: {request.headers.get('Authorization')}")
        print(f"request.user: {request.user}")
        print(f"request.user.is_authenticated: {request.user.is_authenticated}")

        bert_search = BertSearch()
        
        print(f"request.user: {request.user}")
        # 保存用户搜索历史
        if request.user.is_authenticated and query:
            try:
                # 创建搜索历史记录
                UserSearchHistory.objects.create(
                    user=request.user,
                    search_query=query,
                    # vector_embedding=vector_embedding.tolist() if vector_embedding is not None else None
                )
                
                # 保持历史记录在10条以内
                # 获取需要删除的记录的 id
                history_count = UserSearchHistory.objects.filter(user=request.user).count()
                if history_count > 10:
                    records_to_delete = UserSearchHistory.objects.filter(
                        user=request.user
                    ).order_by('search_time').values_list('id', flat=True)[:history_count-10]
                    # 使用 id__in 进行删除
                    UserSearchHistory.objects.filter(id__in=records_to_delete).delete()
                
                print(f"搜索历史已保存")
                    
            except Exception as e:
                print(f"保存搜索历史失败: {str(e)}")

        
        if query and sort == 'relevance':
            try:
                print(f"query: {query}")
                # similar_results = milvus_query.search_similar(query, top_k=20)
                similar_results = bert_search.search_similar(query, top_k=20)
                print(f"向量搜索结果数量: {len(similar_results)}")
                
                # 通过文件名查找文章，并保存匹配的文本
                articles_with_matches = {}
                for result in similar_results:
                    print(f"result: {result}")
                    try:
                        # 直接使用文件名进行匹配
                        articles = Article.objects.filter(file_path__icontains=result.doc_id)
                        for article in articles:
                            if article.id not in articles_with_matches:
                                articles_with_matches[article.id] = {
                                    'article': article,
                                    'matches': [],
                                    'max_score': 0
                                }
                            score = 1 - result.distance
                            articles_with_matches[article.id]['matches'].append({
                                'text': result.text,
                                'score': score
                            })
                            articles_with_matches[article.id]['max_score'] = max(
                                articles_with_matches[article.id]['max_score'],
                                score
                            )
                    except Exception as e:
                        print(f"查找文档出错: {str(e)}")
                        continue
                
                # 转换为列表形式并按最高相似度排序
                articles = []
                for article_id, article_data in articles_with_matches.items():
                    article = article_data['article']
                    article.matched_texts = sorted(
                        article_data['matches'],
                        key=lambda x: x['score'],
                        reverse=True
                    )
                    article.relevance_score = article_data['max_score']  # 添加相关度得分
                    articles.append(article)
                
                # 按相关度得分排序
                articles.sort(key=lambda x: x.relevance_score, reverse=True)
                
                print(f"最终找到的文章数量: {len(articles)}")
                print("文章相关度得分:", [
                    f"{article.title[:30]}... : {article.relevance_score:.4f}"
                    for article in articles[:5]  # 只打印前5篇文章的得分
                ])
                
                if len(articles) == 0:
                    print("没有找到匹配的文章，切换到传统搜索")
                    articles = Article.objects.filter(
                        Q(title__icontains=query) |
                        Q(abstract__icontains=query) |
                        Q(content__icontains=query)
                    )
            
            except Exception as e:
                print(f"向量搜索出错: {str(e)}")
                articles = Article.objects.filter(
                    Q(title__icontains=query) |
                    Q(abstract__icontains=query) |
                    Q(content__icontains=query)
                )

        else:
            # 使用传统搜索
            articles = Article.objects.filter(
                Q(title__icontains=query) |
                Q(abstract__icontains=query) |
                Q(content__icontains=query)
            )

        # 应用分类过滤
        if category:
            articles = articles.filter(category__name=category)
        
        # 应用来源类型过滤
        if source_type:
            articles = articles.filter(source_type=source_type)

        # 排序
        if sort == 'date':
            articles = articles.order_by('-created_at')
        elif sort == 'cited':
            articles = articles.order_by('-citation_count')

        # 分页
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        
        # 如果是 QuerySet，直接使用 paginate_queryset
        # 分页处理部分
        if hasattr(articles, 'model'):
            result_page = paginator.paginate_queryset(articles, request)
            serializer = self.get_serializer(result_page, many=True)
            print(f"返回 QuerySet 结果数量: {len(serializer.data)}")
            return paginator.get_paginated_response(serializer.data)
        else:
            total_count = len(articles)
            start = (page - 1) * page_size
            end = min(start + page_size, total_count)
            result_page = articles[start:end]
            
            serializer = self.get_serializer(result_page, many=True)
            print(f"返回列表结果数量: {len(serializer.data)}")
            
            response_data = {
                'count': total_count,
                'next': f'/api/articles/search/?q={query}&page={page + 1}&sort={sort}' if end < total_count else None,
                'previous': f'/api/articles/search/?q={query}&page={page - 1}&sort={sort}' if page > 1 else None,
                'results': serializer.data
            }
            # print(f"响应数据: {response_data}")
            return Response(response_data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        source_type = request.query_params.get('source_type', '')
        # 添加新的搜索参数
        author = request.query_params.get('author', '')
        date_start = request.query_params.get('date_start', '')
        date_end = request.query_params.get('date_end', '')
        
        sort = request.query_params.get('sort', 'relevance')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        # 添加认证信息调试
        print(f"Authorization header: {request.headers.get('Authorization')}")
        print(f"request.user: {request.user}")
        print(f"request.user.is_authenticated: {request.user.is_authenticated}")

        bert_search = BertSearch()
        
        print(f"request.user: {request.user}")
        # 保存用户搜索历史
        if request.user.is_authenticated and query:
            try:
                
                # 创建搜索历史记录
                UserSearchHistory.objects.create(
                    user=request.user,
                    search_query=query,
                    # vector_embedding=vector_embedding.tolist() if vector_embedding is not None else None
                )
                
                # 保持历史记录在10条以内
                # 修改这部分代码
                # 获取需要删除的记录的 id
                history_count = UserSearchHistory.objects.filter(user=request.user).count()
                if history_count > 10:
                    records_to_delete = UserSearchHistory.objects.filter(
                        user=request.user
                    ).order_by('search_time').values_list('id', flat=True)[:history_count-10]
                    # 使用 id__in 进行删除
                    UserSearchHistory.objects.filter(id__in=records_to_delete).delete()
                
                print(f"搜索历史已保存")
                    
            except Exception as e:
                print(f"保存搜索历史失败: {str(e)}")

        if query and sort == 'relevance':
            try:
                similar_results = bert_search.search_similar(query, top_k=20)
                
                # 通过文件名查找文章
                articles_with_scores = {}
                for result in similar_results:
                    try:
                        articles = Article.objects.filter(file_path__icontains=result.doc_id)
                        for article in articles:
                            if article.id not in articles_with_scores:
                                articles_with_scores[article.id] = {
                                    'article': article,
                                    'score': 1 - result.distance
                                }
                            else:
                                articles_with_scores[article.id]['score'] = max(
                                    articles_with_scores[article.id]['score'],
                                    1 - result.distance
                                )
                    except Exception as e:
                        print(f"查找文档出错: {str(e)}")
                        continue
                
                # 转换为列表并排序
                articles = [
                    item['article'] for item in sorted(
                        articles_with_scores.values(),
                        key=lambda x: x['score'],
                        reverse=True
                    )
                ]
                
                if len(articles) == 0:
                    articles = Article.objects.filter(
                        Q(title__icontains=query) |
                        Q(abstract__icontains=query) |
                        Q(content__icontains=query)
                    )
            
            except Exception as e:
                print(f"向量搜索出错: {str(e)}")
                articles = Article.objects.filter(
                    Q(title__icontains=query) |
                    Q(abstract__icontains=query) |
                    Q(content__icontains=query)
                )

        else:
            # 使用传统搜索
            articles = Article.objects.filter(
                Q(title__icontains=query) |
                Q(abstract__icontains=query) |
                Q(content__icontains=query)
            )        

        # 应用分类过滤
        if category:
            articles = [article for article in articles if article.category.name == category]
        
        # 应用来源类型过滤
        if source_type:
            articles = [article for article in articles if article.source_type.name == source_type]

        # 添加作者过滤
        if author:
            if hasattr(articles, 'model'):
                articles = articles.filter(author__icontains=author)
            else:
                articles = [article for article in articles if author.lower() in article.author.lower()]
        
        # 添加日期范围过滤
        if date_start:
            if hasattr(articles, 'model'):
                articles = articles.filter(created_at__gte=date_start)
            else:
                articles = [article for article in articles if article.created_at and article.created_at.strftime('%Y-%m-%d') >= date_start]
        
        if date_end:
            if hasattr(articles, 'model'):
                articles = articles.filter(created_at__lte=date_end)
            else:
                articles = [article for article in articles if article.created_at and article.created_at.strftime('%Y-%m-%d') <= date_end]

        # 排序
        if sort == 'date':
            articles = articles.order_by('-created_at')
        elif sort == 'cited':
            articles = articles.order_by('-citation_count')

        # 分页
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        
        # 如果是 QuerySet，直接使用 paginate_queryset
        # 分页处理
        if hasattr(articles, 'model'):
            paginator = PageNumberPagination()
            paginator.page_size = page_size
            result_page = paginator.paginate_queryset(articles, request)
            serializer = self.get_serializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            total_count = len(articles)
            start = (page - 1) * page_size
            end = min(start + page_size, total_count)
            result_page = articles[start:end]
            
            serializer = self.get_serializer(result_page, many=True)
            
            # 构建基础URL，包含所有搜索参数
            base_url = f'/api/articles/search/?q={query}&sort={sort}'
            if category:
                base_url += f'&category={category}'
            if source_type:
                base_url += f'&source_type={source_type}'
            if author:
                base_url += f'&author={author}'
            if date_start:
                base_url += f'&date_start={date_start}'
            if date_end:
                base_url += f'&date_end={date_end}'
            
            response_data = {
                'count': total_count,
                'next': f'{base_url}&page={page + 1}' if end < total_count else None,
                'previous': f'{base_url}&page={page - 1}' if page > 1 else None,
                'results': serializer.data
            }
            return Response(response_data)

    @action(detail=False, methods=['get'])
    def category_stats(self, request):
        """获取文献分类统计"""
        query = request.query_params.get('q', '')
        
        # 基础查询
        base_query = Article.objects.filter(
            Q(title__icontains=query) |
            Q(abstract__icontains=query) |
            Q(content__icontains=query)
        )
    
        # 获取分类统计：统计每个分类下符合搜索条件的文章数量
        categories = Category.objects.annotate(
            count=Count('articles', filter=Q(articles__in=base_query))
        ).values('name', 'count')
    
        # 获取来源类型统计：统计每种来源类型下符合搜索条件的文章数量
        source_types = Article.objects.filter(
            id__in=base_query
        ).values('source_type').annotate(
            count=Count('id')
        )
    
        return Response({
            'categories': categories,
            'source_types': source_types
        })

    # @action(detail=False, methods=['get'])
    # def hot(self, request):
    #     articles = Article.objects.order_by('-views')[:10]
    #     serializer = self.get_serializer(articles, many=True)
    #     return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def hot(self, request):
        try:
            # 直接获取预计算的热门文章
            hot_articles = HotArticle.objects.select_related('article').all()
            articles = [ha.article for ha in hot_articles]
            
            serializer = self.get_serializer(articles, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            print(f"获取热门推荐失败: {str(e)}")
            # 发生错误时返回文章
            articles = Article.objects.order_by('-views')[:10]
            serializer = self.get_serializer(articles, many=True)
            return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recommend(self, request):
        if not request.user.is_authenticated:
            articles = Article.objects.order_by('-created_at')[:10]
        else:
            # 获取用户的所有搜索历史，按时间倒序排列
            all_searches = UserSearchHistory.objects.filter(
                user=request.user
            ).order_by('-search_time')

            if not all_searches.exists():
                articles = Article.objects.order_by('-created_at')[:10]
            else:
                bert_search = BertSearch()
                article_scores = {}

                # 计算时间权重
                total_searches = all_searches.count()
                latest_time = all_searches.first().search_time

                for idx, search in enumerate(all_searches):
                    # 计算时间差权重（越近权重越高）
                    time_diff = (latest_time - search.search_time).total_seconds()
                    time_weight = 1.0 / (1.0 + time_diff / 86400)  # 24小时作为基准

                    try:
                        similar_results = bert_search.search_similar(
                            search.search_query,
                            top_k=10
                        )

                        for result in similar_results:
                            article = Article.objects.filter(
                                file_path__icontains=result.doc_id
                            ).first()
                            if article:
                                score = (1 - result.distance) * time_weight
                                if article.id in article_scores:
                                    article_scores[article.id]['score'] += score
                                else:
                                    article_scores[article.id] = {
                                        'article': article,
                                        'score': score
                                    }
                    except Exception as e:
                        print(f"处理搜索历史记录时出错: {str(e)}")
                        continue

                if article_scores:
                    # 按累计得分排序并获取前10篇文章
                    articles = [
                        item['article'] for item in sorted(
                            article_scores.values(),
                            key=lambda x: x['score'],
                            reverse=True
                        )[:10]
                    ]
                else:
                    articles = Article.objects.order_by('-created_at')[:10]

        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        try:
            article = self.get_object()
            serializer = self.get_serializer(article)
            return Response(serializer.data)
        except Article.DoesNotExist:
            return Response({"error": "文章不存在"}, status=404)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载文章全文PDF"""
        article = self.get_object()
        
        if not article.file_path:
            return Response({"error": "文献文件不存在"}, status=404)
        
        try:
            file_path = article.file_path.path
            if os.path.exists(file_path):
                with open(file_path, 'rb') as pdf:
                    response = HttpResponse(pdf.read(), content_type='application/pdf')
                    filename = f'{article.title}.pdf'
                    filename = filename.encode('utf-8').decode('latin-1')
                    
                    encoded_filename = quote(filename)
                    content_disposition = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
                    response['Content-Disposition'] = content_disposition
                    return response
            else:
                return Response({"error": "文件不存在"}, status=404)
        except Exception as e:
            return Response({"error": f"下载失败: {str(e)}"}, status=500)

    @action(detail=True, methods=['get'])
    def cite(self, request, pk=None):
        """获取引用格式"""
        article = self.get_object()
        
        # 生成引用格式（可以根据需要修改）
        citation = f"{article.author}. {article.title}. {article.source}, {article.publication_date.year}."
        
        return Response(citation)

    @action(detail=True, methods=['post'])
    def collect(self, request, pk=None):
        """收藏文章"""
        article = self.get_object()
        user = request.user
        
        # 检查是否已收藏
        collection, created = Collection.objects.get_or_create(
            user=user,
            article=article
        )
        
        message = "收藏成功" if created else "已经收藏过了"
        return Response({"message": message})

    @action(detail=True, methods=['get'])
    def graph(self, request, pk=None):
        """获取文献关系图谱数据"""
        article = self.get_object()
        
        try:
            bert_search = BertSearch()
            
            # 使用文章标题和关键词作为搜索内容
            search_text = f"{article.title} {article.keywords}"

            similar_results = bert_search.search_similar(
                search_text,
                top_k=10  # 获取前10个相似结果
            )
            
            # 构建图谱数据
            nodes = [
                {
                    'id': str(article.id),
                    'name': article.title,
                    'symbolSize': 50,
                    'category': 0
                }
            ]
            
            links = []
            added_articles = set([article.id])  # 用于去重
            
            # 添加相关文章节点和连接
            for result in similar_results:
                related_article = Article.objects.filter(
                    file_path__icontains=result.doc_id
                ).first()
                
                if related_article and related_article.id not in added_articles:
                    # 计算相似度得分
                    similarity_score = 1 - result.distance
                    
                    # 只添加相似度大于0.3的文章
                    if similarity_score > 0.3:
                        nodes.append({
                            'id': str(related_article.id),
                            'name': related_article.title,
                            'symbolSize': 30 + (similarity_score * 20),  # 根据相似度调整节点大小
                            'category': 1
                        })
                        
                        links.append({
                            'source': str(article.id),
                            'target': str(related_article.id),
                            'value': f'相似度: {similarity_score:.2f}',
                            'symbolSize': 1 + (similarity_score * 4)  # 根据相似度调整连线粗细
                        })
                        
                        added_articles.add(related_article.id)
                        
                        # 控制相关文章数量在5-10篇之间
                        if len(added_articles) >= 10:
                            break
            
            return Response({
                'nodes': nodes,
                'links': links
            })
            
        except Exception as e:
            print(f"生成文献关系图谱失败: {str(e)}")
            # 发生错误时返回基于分类的相关文章
            related_articles = Article.objects.filter(
                category=article.category
            ).exclude(id=article.id)[:5]
            
            # 构建基础图谱数据
            nodes = [
                {
                    'id': str(article.id),
                    'name': article.title,
                    'symbolSize': 50,
                    'category': 0
                }
            ]
            
            links = []
            
            for related in related_articles:
                nodes.append({
                    'id': str(related.id),
                    'name': related.title,
                    'symbolSize': 30,
                    'category': 1
                })
                links.append({
                    'source': str(article.id),
                    'target': str(related.id),
                    'value': '同类文献'
                })
            
            return Response({
                'nodes': nodes,
                'links': links
            })

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    permission_classes = [AllowAny]
