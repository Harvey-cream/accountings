from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class UserloginView(APIView):
    def get(self, request, format=None):
        return Response("登陆成功", status=status.HTTP_200_OK)

    def post(self, request, format=None):
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        
        if not mobile or not password:
            return Response({"message": "手机号和密码不能为空", "code": 400}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(mobile=mobile)
            # 校验加密后的密码
            if check_password(password, user.password):
                # 更新最后登录时间

                user.last_login_time = timezone.now()
                user.save()
                
                return Response({
                    "message": "登录成功",
                    "code": 200,
                    "data": {
                        "userId": user.id,
                        "username": user.username,
                        "mobile": user.mobile,
                        "avatarUrl": user.avatar_url
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"message": "密码错误", "code": 400}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"message": "用户不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)


class UserRegisterView(APIView):
    def post(self, request, format=None):
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        print(f"后端收到注册请求：mobile={mobile}")
        
        if not mobile or not password:
            return Response({"message": "手机号和密码不能为空", "code": 400}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(mobile=mobile).exists():
            return Response({"message": "该手机号已注册", "code": 400}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 创建用户并对密码进行加密存储
            user = User.objects.create(
                mobile=mobile,
                password=make_password(password), # 推荐加密存储
                username=mobile # 初始姓名默认为手机号
            )
            print(f"用户 {mobile} 已存入数据库，分配 ID: {user.id}")
            return Response({"message": "注册成功", "code": 200}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"注册失败: {str(e)}", "code": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
