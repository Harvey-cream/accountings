from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from django.utils import timezone
from datetime import datetime, timedelta
from .utils.sm2 import request_handler, sm3_hash, get_refer_code
from .utils.jwt_token import create_token, verify_token
from user.utils.user import get_current_user
from common.response_web import HttpResult, WebStatusEnum

class UserloginView(APIView):
    def get(self, request, format=None):
        return HttpResult.success("登录成功")

    def post(self, request, format=None):
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        
        if not mobile or not password:
            return HttpResult.fail("手机号和密码不能为空")
            
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
                    'userId': user.id,
                    'username': user.username if user.username else user.mobile,
                    'mobile': user.mobile,
                    'loginType': user.login_type,
                    'selfCode': user.self_code,
                    'avatarUrl': user.avatar_url,
                    'isVerified': user.is_verified,
                }
                
                return HttpResult.success_with_data("登录成功", {
                    'token_info': token_info,
                    'user_info': user_info
                })
            else:
                return HttpResult.fail("密码错误")
        except User.DoesNotExist:
            return HttpResult.fail("用户不存在")
        except Exception as e:
            print(f"登录异常: {e}")
            return HttpResult.fail(f"登录失败: {str(e)}")


class RefreshTokenView(APIView):
    """刷新 Token 接口"""
    def post(self, request, format=None):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return HttpResult.fail("刷新令牌不能为空")
            
        # 1. 验证旧的 Token (返回 user_id)
        user_id = verify_token(refresh_token)
        if not user_id:
            return HttpResult.fail("Token 已失效，请重新登录")
            
        try: 
            user = User.objects.get(id=user_id, is_active=True) 
        except User.DoesNotExist: 
            return HttpResult.fail('用户不存在或已被禁用') 
        except Exception as e:
            return HttpResult.fail(f'刷新异常: {str(e)}')
            
        # 2. 生成新 Token (10 分钟) 和保持旧的 Refresh Token (或者生成新的)
        # 这里简单起见，生成新的 Access Token，保持原有的 Refresh Token 或者也更新
        new_token = create_token(user_id, minutes=10)
        token_expires = datetime.now() + timedelta(minutes=10)
        
        # 为了保持前端 sessionInfo.token_info 的完整性，返回完整对象
        token_info = {
            'token': new_token,
            'refresh': refresh_token, # 继续使用当前的刷新令牌
            'expires': int(token_expires.timestamp() * 1000),
        }
        
        print(f"Token 刷新成功: 用户 ID={user_id}, 新 Token 前缀={new_token[:10]}...")
        return HttpResult.success_with_data('刷新token成功', token_info)


class UserRegisterView(APIView):
    def post(self, request, format=None):
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        refer_code = request.data.get('refer_code') # 前端传来的推荐码
        
        if not mobile or not password:
            return HttpResult.fail("手机号和密码不能为空")
        
        if User.objects.filter(mobile=mobile).exists():
            return HttpResult.fail("该手机号已注册")
        
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


class GetUserInfoView(APIView):
    """获取用户信息接口"""
    def get(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
        
        user_info = {
            'userId': user.id,
            'username': user.username if user.username else user.mobile,
            'mobile': user.mobile,
            'loginType': user.login_type,
            'selfCode': user.self_code,
            'avatarUrl': user.avatar_url,
            'isVerified': user.is_verified,
        }
        return HttpResult.success_with_data("获取成功", user_info)
