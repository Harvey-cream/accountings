from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from django.utils import timezone
from datetime import datetime, timedelta
from .utils.sm2 import request_handler, sm3_hash, get_refer_code
from .utils.jwt_token import create_token, verify_token
from common.response_web import HttpResult, WebStatusEnum

class UserloginView(APIView):
    def get(self, request, format=None):
        return HttpResult.success("登录成功")

    def post(self, request, format=None):
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        
        if not mobile or not password:
            return HttpResult.fail("手机号和密码不能为空", code=WebStatusEnum.PARAM_ERROR.code)
            
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
                
                # 构造详细用户信息
                user_info = {
                    'user_id': user.id,
                    'username': user.username if user.username else user.mobile,
                    'mobile': user.mobile,
                    'login_type': user.login_type,
                    'self_code': user.self_code,
                    'avatar_url': user.avatar_url,
                    'is_verified': user.is_verified,
                }
                
                return HttpResult.success_with_data("登录成功", {
                    'token_info': token_info,
                    'user_info': user_info
                })
            else:
                return HttpResult.fail("密码错误", code=WebStatusEnum.PARAM_ERROR.code)
        except User.DoesNotExist:
            return HttpResult.fail("用户不存在", code=WebStatusEnum.NOT_FOUND.code)
        except Exception as e:
            print(f"登录异常: {e}")
            return HttpResult.fail(f"登录失败: {str(e)}")


class RefreshTokenView(APIView):
    """刷新 Token 接口"""
    def post(self, request, format=None):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return HttpResult.fail("刷新令牌不能为空", code=WebStatusEnum.PARAM_ERROR.code)
        
        # 验证刷新令牌 (1周内有效)
        payload = verify_token(refresh_token, expect_refresh=True)
        if not payload:
            return HttpResult.fail("刷新令牌已失效，请重新登录", code=WebStatusEnum.UNAUTHORIZED.code)
        
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
        
        return HttpResult.success_with_data("刷新成功", token_info)


class UserRegisterView(APIView):
    def post(self, request, format=None):
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        refer_code = request.data.get('refer_code') # 前端传来的推荐码
        
        if not mobile or not password:
            return HttpResult.fail("手机号和密码不能为空", code=WebStatusEnum.PARAM_ERROR.code)
        
        if User.objects.filter(mobile=mobile).exists():
            return HttpResult.fail("该手机号已注册", code=WebStatusEnum.PARAM_ERROR.code)
        
        try:
            # 1. 解密前端 SM2 加密的密码
            decrypted_password = request_handler.decrypt(password)
            # 2. 生成用户自身的邀请码
            self_code = get_refer_code()
            
            # 3. 创建用户，存入 SM3 哈希后的密码 (加盐处理)
            user = User.objects.create(
                mobile=mobile,
                username=mobile,
                refer_code=refer_code,
                self_code=self_code,
                password=sm3_hash(decrypted_password)
            )
            return HttpResult.success("注册成功")
        except Exception as e:
            print(f"用户注册失败: {e}")
            return HttpResult.fail("注册失败")
