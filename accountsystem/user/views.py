from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from django.utils import timezone
from datetime import datetime, timedelta
from .utils.sm2 import request_handler, sm3_hash, get_refer_code
from .utils.jwt_token import create_token, verify_token

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
            decrypted_password = request_handler.decrypt(password)
            if sm3_hash(decrypted_password) == user.password:
                user.last_login_time = timezone.now()
                user.save()
                token = create_token(user.id)
                refresh_token = create_token(user.id)

                token_expires = datetime.now() + timedelta(minutes=10)
                refresh_expires = datetime.now() + timedelta(weeks=1)
                
                token_info = {
                    'token': token,
                    'refresh': refresh_token,
                    'expires': int(token_expires.timestamp() * 1000),
                    'refresh_expires': int(refresh_expires.timestamp() * 1000),
                }
                
                return Response({
                    "message": "登录成功",
                    "code": 200,
                    "token_info": token_info,
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
        except Exception as e:
            print(f"登录异常: {e}")
            return Response({"message": f"登录失败: {str(e)}", "code": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefreshTokenView(APIView):
    """刷新 Token 接口"""
    def post(self, request, format=None):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({"message": "刷新令牌不能为空", "code": 400}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证刷新令牌 (1周内有效)
        payload = verify_token(refresh_token, expect_refresh=True)
        if not payload:
            return Response({"message": "刷新令牌已失效，请重新登录", "code": 401}, status=status.HTTP_401_UNAUTHORIZED)
        
        user_id = payload.get('user_id')
        refresh_expires = payload.get('exp') # 原始刷新令牌的过期时间
        
        # 生成新的 Access Token (延续 10 分钟)
        new_token, new_expires = create_token(user_id, minutes=10)
        
        token_info = {
            'token': new_token,
            'refresh': refresh_token, # 保持使用当前的刷新令牌
            'expires': int(new_expires * 1000),
            'refresh_expires': int(refresh_expires * 1000),
        }
        
        return Response({
            "message": "刷新成功",
            "code": 200,
            "token_info": token_info
        }, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    def post(self, request, format=None):
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        refer_code = request.data.get('refer_code') # 前端传来的推荐码
        
        if not mobile or not password:
            return Response({"message": "手机号和密码不能为空", "code": 400}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(mobile=mobile).exists():
            return Response({"message": "该手机号已注册", "code": 400}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 1. 解密前端 SM2 加密的密码
            decrypted_password = request_handler.decrypt(password)
            # 2. 生成用户自身的邀请码
            self_code = get_refer_code()
            
            # 3. 创建用户，存入 SM3 哈希后的密码
            user = User.objects.create(
                mobile=mobile,
                username=mobile,
                refer_code=refer_code,
                self_code=self_code,
                password=sm3_hash(decrypted_password)
            )
            return Response({"message": "注册成功", "code": 200}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"用户注册失败: {e}")
            return Response({"message": "注册失败", "code": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
