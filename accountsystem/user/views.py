from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, UserCheckIn, Medal, UserMedal
from .serializers import MedalSerializer
from django.utils import timezone
from account.models import TransactionRecord
from datetime import datetime, timedelta
from django.db.models import Count, Q
from .utils.sm2 import request_handler, sm3_hash, get_refer_code
from .utils.jwt_token import create_token, verify_token
from user.utils.user_utils import get_current_user
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

class GetMedalListView(APIView):
    """获取勋章列表（包含解锁状态和进度）"""
    def get(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
            
        medals = Medal.objects.all().order_by('sort_order')
        serializer = MedalSerializer(medals, many=True, context={'request': request})
        
        # 勋章列表
        medal_list = serializer.data
        print(medal_list)
        # 获取当前进度数据
        # 1. 打卡进度
        continuous_checkin = UserCheckIn.objects.filter(user=user).count()
        
        # 2. 记账进度
        total_records = TransactionRecord.objects.filter(user=user).count()
        
        # 3. 资产进度
        from account.models import AssetAccount
        total_assets = AssetAccount.objects.filter(user=user).count()
        
        # 4. 预算进度
        from account.models import TransactionBudget
        has_budget = TransactionBudget.objects.filter(user=user).exists()
        
        # 动态添加进度信息
        for i, medal_data in enumerate(medal_list):
            medal_obj = medals[i]
            req_type = medal_obj.requirement_type
            req_val = medal_obj.requirement_value
            
            current_val = 0
            if req_type == 'checkin':
                current_val = continuous_checkin
            elif req_type == 'bill':
                current_val = total_records
            elif req_type == 'budget':
                current_val = 1 if has_budget else 0
            elif req_type == 'asset':
                current_val = total_assets
                
            medal_data['progress'] = {'current': current_val, 'total': req_val}
            
            # 被动解锁逻辑：如果进度已达标且尚未解锁，则自动创建解锁记录
            if current_val >= req_val and not medal_data['unlocked']:
                UserMedal.objects.get_or_create(user=user, medal=medal_obj)
                medal_data['unlocked'] = True
                from django.utils import timezone
                medal_data['unlock_time'] = timezone.now().strftime('%Y-%m-%d %H:%M')
        
        # 将结果按分类分组，适配前端展示
        categories = {}
        for medal in medal_list:
            cat_name = medal['category']
            if cat_name not in categories:
                categories[cat_name] = []
            categories[cat_name].append(medal)
            
        formatted_data = []
        for cat_name, items in categories.items():
            formatted_data.append({
                'title': cat_name,
                'items': items
            })
            
        return HttpResult.success_with_data("获取勋章成功", formatted_data)

class UserCheckInView(APIView):
    """用户打卡接口"""
    def post(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败")
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # 1. 检查今日是否已打卡
        if UserCheckIn.objects.filter(user=user, date=today).exists():
            return HttpResult.fail("今日已打卡")
            
        last_checkin = UserCheckIn.objects.filter(user=user).order_by('-date').first()
        
        # 2. 检查连续性：如果上一条记录不是昨天，则清空之前的所有打卡记录重新开始
        if last_checkin and last_checkin.date != yesterday:
            UserCheckIn.objects.filter(user=user).delete()
            continuous_days = 1
        else:
            # 获取当前连续天数并+1
            continuous_days = UserCheckIn.objects.filter(user=user).count() + 1
            
        UserCheckIn.objects.create(user=user, date=today)
        
        # 3. 自动解锁勋章逻辑：从数据库获取所有打卡类勋章
        checkin_medals = Medal.objects.filter(requirement_type='checkin').order_by('requirement_value')
        
        new_unlocked_medals = []
        for medal in checkin_medals:
            if continuous_days >= medal.requirement_value:
                # 尝试解锁该勋章
                _, created = UserMedal.objects.get_or_create(user=user, medal=medal)
                if created:
                    new_unlocked_medals.append({
                        'id': medal.id,
                        'name': medal.name,
                        'icon': medal.icon,
                        'description': medal.description
                    })
        
        # 4. 获取下一个勋章的进度
        next_medal = None
        for medal in checkin_medals:
            if continuous_days < medal.requirement_value:
                next_medal = {
                    'required_days': medal.requirement_value,
                    'current_days': continuous_days
                }
                break
                
        return HttpResult.success_with_data("打卡成功", {
            'continuous_days': continuous_days,
            'new_unlocked_medals': new_unlocked_medals,
            'next_progress': next_medal
        })

class GetUserStatsView(APIView):
    """获取用户统计数据（连续打卡、连续记账、总笔数）"""
    def get(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败")
            
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # 1. 连续打卡天数 (直接查表总数，因为断了就会清空)
        # 先做一次过期检查
        last_checkin = UserCheckIn.objects.filter(user=user).order_by('-date').first()
        if last_checkin and last_checkin.date not in [today, yesterday]:
            UserCheckIn.objects.filter(user=user).delete()
            continuous_checkin = 0
        else:
            continuous_checkin = UserCheckIn.objects.filter(user=user).count()

        # 2. 记账总笔数
        total_records = TransactionRecord.objects.filter(user=user).count()
        
        # 3. 连续记账天数
        # 获取用户所有不重复的记账日期，按倒序排
        record_dates = TransactionRecord.objects.filter(user=user).values_list('date', flat=True).distinct().order_by('-date')
        
        continuous_accounting = 0
        if record_dates:
            # 必须从今天或昨天开始算连续
            if record_dates[0] in [today, yesterday]:
                continuous_accounting = 1
                for i in range(len(record_dates) - 1):
                    # 判断是否连续
                    if (record_dates[i] - record_dates[i+1]).days == 1:
                        continuous_accounting += 1
                    else:
                        break
            else:
                # 即使有记录，但如果不包含今天或昨天，连续记账也清0
                continuous_accounting = 0
                
        return HttpResult.success_with_data("获取统计成功", {
            "continuousCheckIn": continuous_checkin,
            "continuousAccounting": continuous_accounting,
            "totalRecords": total_records,
            "isCheckedIn": UserCheckIn.objects.filter(user=user, date=today).exists()
        })
