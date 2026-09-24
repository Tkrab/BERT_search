"""
URL configuration for literature_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, GroupViewSet
from articles.views import ArticleViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'articles', ArticleViewSet)

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),
    
    # 添加前端页面的路由
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('search/', TemplateView.as_view(template_name='search_results.html'), name='search'),
    path('article/<int:id>/', TemplateView.as_view(template_name='article_detail.html'), name='article_detail'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('admin/', TemplateView.as_view(template_name='admin.html'), name='admin'),  # 我们的自定义管理界面
]
