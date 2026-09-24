from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import User

class UserSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_vip', 'is_staff', 'groups', 'password')
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},  # 修改密码字段为非必需
            'groups': {'required': False},
            'username': {'required': False},  # 更新时用户名非必需
            'email': {'required': False}  # 更新时邮箱非必需
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        # 只更新提供的字段
        for attr, value in validated_data.items():
            if attr == 'password' and value:
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    users = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='user_set')

    class Meta:
        model = Group
        fields = ['id', 'name', 'member_count', 'users']

    def get_member_count(self, obj):
        return obj.user_set.count()  # 移除 .all()

# class UserSerializer(serializers.ModelSerializer):
#     groups = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=Group.objects.all(),
#         required=False
#     )

#     class Meta:
#         model = User
#         fields = ('id', 'username', 'email', 'phone', 'is_vip', 'is_staff', 'groups', 'password')
#         extra_kwargs = {
#             'password': {'write_only': True},
#             'groups': {'required': False}
#         }

#     def create(self, validated_data):
#         user = User.objects.create_user(**validated_data)
#         return user