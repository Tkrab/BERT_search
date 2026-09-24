from django.contrib.auth.models import AbstractUser, Group
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_vip = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # 添加创建时间字段
    
    class Meta:
        ordering = ['-created_at']  # 按创建时间倒序排序
        
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='user_set',
        related_query_name='user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='custom_user_set',
        help_text='Specific permissions for this user.',
    )

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
