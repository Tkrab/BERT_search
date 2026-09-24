from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import Group
from .models import User
from .serializers import UserSerializer, GroupSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'login']:
            permission_classes = [AllowAny]
        elif self.action in ['update', 'partial_update', 'change_password']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            serializer = self.get_serializer(user)
            return Response({
                'token': str(refresh.access_token),
                **serializer.data
            })
        return Response(
            {'error': '用户名或密码错误'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # 允许管理员修改任何用户的信息，普通用户只能修改自己的信息
        if not request.user.is_staff and instance.id != request.user.id:
            return Response(
                {'error': '无权修改其他用户的信息'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_role(self, request, pk=None):
        user = self.get_object()
        is_staff = request.data.get('is_staff', False)
        
        user.is_staff = is_staff
        user.save()
        
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        
        # 确保用户只能修改自己的密码
        if user.id != request.user.id:
            return Response(
                {'error': '无权修改其他用户的密码'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(current_password):
            return Response(
                {'error': '当前密码错误'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': '密码修改成功'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_group(self, request, pk=None):
        user = self.get_object()
        group_id = request.data.get('group_id')
        
        # 清除现有用户组
        user.groups.clear()
        
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
            except Group.DoesNotExist:
                return Response(
                    {'error': '用户组不存在'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({'message': '用户组更新成功'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_vip(self, request, pk=None):
        user = self.get_object()
        user.is_vip = not user.is_vip
        user.save()
        return Response({'is_vip': user.is_vip})

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        group = serializer.save()
        # 根据组名设置用户权限
        if group.name.lower() in ['admin', 'administrator', '管理员']:
            for user in group.user_set.all():
                user.is_staff = True
                user.save()
        else:
            for user in group.user_set.all():
                user.is_staff = False
                user.save()

    @action(detail=True, methods=['post'])
    def add_members(self, request, pk=None):
        group = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        try:
            users = User.objects.filter(id__in=user_ids)
            group.user_set.add(*users)
            
            # 更新用户权限
            is_admin_group = group.name.lower() in ['admin', 'administrator', '管理员']
            for user in users:
                user.is_staff = is_admin_group
                user.save()
                
            return Response({'message': '成员添加成功'})
        except Exception as e:
            return Response(
                {'error': f'添加成员失败: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def remove_members(self, request, pk=None):
        group = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        try:
            users = User.objects.filter(id__in=user_ids)
            group.user_set.remove(*users)
            
            # 移除管理员权限
            for user in users:
                if group.name.lower() in ['admin', 'administrator', '管理员']:
                    user.is_staff = False
                    user.save()
                    
            return Response({'message': '成员移除成功'})
        except Exception as e:
            return Response(
                {'error': f'移除成员失败: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    