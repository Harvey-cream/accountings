from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, UserCheckIn, Medal, UserMedal, UserPointRecord
from .serializers import MedalSerializer
from django.utils import timezone
from account.models import TransactionRecord
from datetime import datetime, timedelta
from django.db.models import Count, Q, Sum, Min, Max
from .utils.sm2 import request_handler, sm3_hash, get_refer_code
from .utils.jwt_token import create_token, verify_token
from user.utils.user_utils import get_current_user, upload_to_oss, sign_oss_url
from common.response_web import HttpResult, WebStatusEnum
from django.db import transaction
from user.utils.tools import generate_account_id, generate_qr_base64
import os
import uuid
from django.conf import settings

class UploadAvatarView(APIView):
    """用户上传文件接口 (支持头像和其他业务图片)"""
    def post(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
            
        file_obj = request.FILES.get('file')
        # 获取上传目录，默认为 avatars
        folder = request.POST.get('folder', 'avatars')
        
        if not file_obj:
            return HttpResult.fail("请选择图片文件")
        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            return HttpResult.fail("仅支持 jpg, png, gif 格式的图片")
        if file_obj.size > 2 * 1024 * 1024:
            return HttpResult.fail("图片大小不能超过 2MB")  
        try:
            # 使用阿里云 OSS 上传
            oss_path = upload_to_oss(file_obj, folder=folder)
            
            if not oss_path:
                return HttpResult.fail("上传到云存储失败")
                
            # 如果是上传头像，则更新用户信息
            if folder == 'avatars':
                user.avatar_url = oss_path
                user.save()
            
            # 生成带签名的 URL 给前端显示
            full_url = sign_oss_url(oss_path)
            
            return HttpResult.success_with_data("上传成功", {
                "url": full_url, # 通用返回字段
                "avatarUrl": full_url, # 兼容旧版头像逻辑
                "ossPath": oss_path # 返回原始路径供后续业务存储
            })
            
        except Exception as e:
            print(f"上传文件异常: {e}")
            return HttpResult.fail(f"上传失败: {str(e)}")

class GetInviteQRView(APIView):
    """获取邀请二维码（Base64格式）"""
    def get(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
            
        # 1. 构造邀请链接 (线上正式地址)
        # 携带用户自身的邀请码 self_code
        invite_url = f"https://draccounting.xin/?refer_code={user.self_code}#/"
        
        # 2. 调用工具函数生成二维码 Base64
        qr_base64 = generate_qr_base64(invite_url)
        
        return HttpResult.success_with_data("生成二维码成功", {
            "qr_base64": qr_base64,
            "invite_url": invite_url,
            "refer_code": user.self_code
        })

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
                
                # 4. 如果 account_id 为空（兼容老用户），则自动生成
                if not user.account_id:
                    user.account_id = generate_account_id(User)
                    user.save()

                # 格式化头像地址 (生成签名 URL)
                avatar_url = sign_oss_url(user.avatar_url)

                # 5. 构造详细用户信息
                user_info = {
                    'userId': user.id,
                    'username': user.username if user.username else user.mobile,
                    'nickname': user.nickname if user.nickname else (user.username if user.username else user.mobile),
                    'accountId': user.account_id,
                    'signature': user.signature,
                    'gender': user.gender,
                    'mobile': user.mobile,
                    'loginType': user.login_type,
                    'selfCode': user.self_code,
                    'avatarUrl': avatar_url,
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
            
        # 1. 验证旧的 Token (获取完整 payload 以便检查过期时间)
        payload = verify_token(refresh_token, expect_refresh=True)
        if not payload:
            return HttpResult.fail("Token 已失效，请重新登录")
        
        user_id = payload.get('user_id')
        exp_timestamp = payload.get('exp')
            
        try: 
            user = User.objects.get(id=user_id, is_active=True) 
        except User.DoesNotExist: 
            return HttpResult.fail('用户不存在或已被禁用') 
        except Exception as e:
            return HttpResult.fail(f'刷新异常: {str(e)}')
            
        # 2. 生成新 Access Token (10 分钟)
        new_token = create_token(user_id, minutes=10)
        token_expires = datetime.now() + timedelta(minutes=10)
        
        # 3. 检查 Refresh Token 并且返回完整对象
        now_ts = int(datetime.now(timezone.utc).timestamp())
        remaining_days = (exp_timestamp - now_ts) / (24 * 3600)
        
        new_refresh_token = refresh_token # 默认沿用旧的
        refresh_expires_ts = exp_timestamp * 1000 # 默认沿用旧的过期时间
        
        if remaining_days < 1:
            new_refresh_token = create_token(user_id) # 续期 1 周
            refresh_expires_ts = int((datetime.now() + timedelta(weeks=1)).timestamp() * 1000)
            print(f"用户={user_id} 的 Refresh Token 即将到期 (剩余 {remaining_days:.1f} 天)，已自动续期一周")
        
        token_info = {
            'token': new_token,
            'refresh': new_refresh_token,
            'expires': int(token_expires.timestamp() * 1000),
            'refresh_expires': refresh_expires_ts,
        }
        
        print(f"Token 刷新成功: 用户 ID={user_id}, 新 Token 前缀={new_token[:10]}...")
        return HttpResult.success_with_data('刷新token成功', token_info)


class UserRegisterView(APIView):
    def post(self, request, format=None):
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        nickname = request.data.get('nickname')
        refer_code = request.data.get('refer_code') # 前端传来的推荐码
        
        if not mobile or not password:
            return HttpResult.fail("手机号和密码不能为空")
        
        if not nickname:
            return HttpResult.fail("昵称不能为空")
        
        if User.objects.filter(mobile=mobile).exists():
            return HttpResult.fail("该手机号已注册")
        
        try:
            # 1. 解密前端 SM2 加密的密码
            decrypted_password = request_handler.decrypt(password)
            # 2. 生成用户自身的邀请码
            self_code = get_refer_code()
            # 3. 生成唯一的账号 ID
            account_id = generate_account_id(User)
            
            # 4. 创建用户，存入 SM3 哈希后的密码 (加盐处理)
            user = User.objects.create(
                mobile=mobile,
                username=nickname, # 默认真实姓名也先存昵称
                nickname=nickname,
                account_id=account_id,
                refer_code=refer_code,
                self_code=self_code,
                password=sm3_hash(decrypted_password)
            )
            return HttpResult.success("注册成功")
        except Exception as e:
            print(f"用户注册失败: {e}")
            return HttpResult.fail("注册失败")


class GetUserInfoView(APIView):
    """获取用户信息接口 (支持获取他人信息)"""
    def get(self, request, format=None):
        current_user = get_current_user(request)
        user_id = request.query_params.get('userId')
        
        if user_id and user_id != 'self':
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return HttpResult.fail("用户不存在")
        else:
            user = current_user
            
        if not user:
            return HttpResult.fail("未登录且未指定用户ID")
        
        # 如果 account_id 为空（兼容老用户），则自动生成
        if not user.account_id:
            user.account_id = generate_account_id(User)
            user.save()

        # 获取社交统计数据 (延迟导入避免循环依赖)
        from comment.models import UserFollow, UserPost, UserPostLike
        
        following_count = UserFollow.objects.filter(user=user).count()
        followers_count = UserFollow.objects.filter(followed_user=user).count()
        
        # 获赞与收藏 (暂时只算获赞)
        # 1. 该用户发布的帖子获得的点赞总数
        posts = UserPost.objects.filter(user=user)
        likes_received = UserPostLike.objects.filter(post__in=posts).count()
        
        # 检查当前登录用户是否关注了目标用户
        is_followed = False
        if current_user and current_user.id != user.id:
            is_followed = UserFollow.objects.filter(user=current_user, followed_user=user).exists()

        # 格式化头像地址 (生成签名 URL)
        avatar_url = sign_oss_url(user.avatar_url)

        user_info = {
            'userId': user.id,
            'username': user.username if user.username else user.mobile,
            'nickname': user.nickname if user.nickname else (user.username if user.username else user.mobile),
            'accountId': user.account_id,
            'signature': user.signature,
            'gender': user.gender,
            'mobile': user.mobile,
            'loginType': user.login_type,
            'selfCode': user.self_code,
            'avatarUrl': avatar_url,
            'isVerified': user.is_verified,
            'isSelf': current_user.id == user.id if current_user else False,
            'following': following_count,
            'followers': followers_count,
            'likesAndCollects': likes_received,
            'isFollowed': is_followed
        }
        return HttpResult.success_with_data("获取成功", user_info)

class UpdateUserInfoView(APIView):
    """修改用户信息接口"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
            
        nickname = request.data.get('nickname')
        signature = request.data.get('signature')
        gender = request.data.get('gender')
        
        # 账号 ID 不允许修改，这里不处理 account_id
        
        if nickname is not None:
            if not nickname.strip():
                return HttpResult.fail("昵称不能为空")
            user.nickname = nickname
            
        if signature is not None:
            user.signature = signature
            
        if gender is not None:
            if gender not in ['men', 'women']:
                return HttpResult.fail("性别格式错误")
            user.gender = gender
            
        user.save()
        
        # 格式化头像地址 (生成签名 URL)
        avatar_url = sign_oss_url(user.avatar_url)

        # 返回更新后的信息
        user_info = {
            'userId': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'accountId': user.account_id,
            'signature': user.signature,
            'gender': user.gender,
            'mobile': user.mobile,
            'avatarUrl': avatar_url,
        }
        
        return HttpResult.success_with_data("修改成功", user_info)

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
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # 1. 打卡进度 (改用日期比对逻辑计算真实连续天数)
        checkin_dates = UserCheckIn.objects.filter(
            user=user, 
            date__lte=today
        ).order_by('-date').values_list('date', flat=True)
        
        continuous_checkin = 0
        if checkin_dates:
            # 判断最后一次打卡是否是今天或昨天
            if checkin_dates[0] == today or checkin_dates[0] == yesterday:
                continuous_checkin = 1
                current_date = checkin_dates[0]
                for i in range(1, len(checkin_dates)):
                    if (current_date - checkin_dates[i]).days == 1:
                        continuous_checkin += 1
                        current_date = checkin_dates[i]
                    else:
                        break
        
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
    """用户打卡接口（仅处理打卡和勋章）"""
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
        
        # 2. 检查连续性并计算天数
        with transaction.atomic():
            if last_checkin and last_checkin.date != yesterday:
                # 连续性断掉，清空之前记录并重新开始
                UserCheckIn.objects.filter(user=user).delete()
                continuous_days = 1
            else:
                # 保持连续，天数+1
                continuous_days = UserCheckIn.objects.filter(user=user).count() + 1
                
            UserCheckIn.objects.create(user=user, date=today)
        
        # 3. 自动解锁勋章逻辑
        checkin_medals = Medal.objects.filter(requirement_type='checkin').order_by('requirement_value')
        
        new_unlocked_medals = []
        for medal in checkin_medals:
            if continuous_days >= medal.requirement_value:
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

class UserPointSignInView(APIView):
    """用户签到领积分接口"""
    def post(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败")
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # 1. 检查今日是否已领过积分
        if UserPointRecord.objects.filter(user=user, type='checkin', create_time__date=today).exists():
            return HttpResult.fail("今日已签到")
            
        # 2. 计算连续签到天数（基于积分流水，只统计到昨天）
        last_record = UserPointRecord.objects.filter(
            user=user, 
            type='checkin', 
            create_time__date__lte=yesterday
        ).order_by('-create_time').first()
        
        streak_days = 1
        if last_record and last_record.create_time.date() == yesterday:
            records = UserPointRecord.objects.filter(
                user=user, 
                type='checkin', 
                create_time__date__lt=today
            ).order_by('-create_time')[:7]
            current_date = yesterday
            for rec in records:
                if rec.create_time.date() == current_date:
                    streak_days += 1
                    current_date -= timedelta(days=1)
                else:
                    break
        
        # 3. 积分计算逻辑
        points_to_add = min(1 + streak_days, 6)
        
        with transaction.atomic():
            # 记录积分流水
            UserPointRecord.objects.create(
                user=user,
                amount=points_to_add,
                direction='income',
                type='checkin',
                description=f"连续签到{streak_days}天奖励"
            )
            
        # 计算最新总积分
        points_stats = UserPointRecord.objects.filter(user=user).aggregate(
            income=Sum('amount', filter=Q(direction='income')),
            expense=Sum('amount', filter=Q(direction='expense'))
        )
        total_points = (points_stats['income'] or 0) - (points_stats['expense'] or 0)
        
        return HttpResult.success_with_data("签到成功", {
            'streak_days': streak_days,
            'points_earned': points_to_add,
            'total_points': total_points
        })

class GetUserPointsView(APIView):
    """获取用户积分数据（动态计算流水）"""
    def get(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败")
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # 动态计算总积分：收入 - 支出
        points_stats = UserPointRecord.objects.filter(user=user).aggregate(
            income=Sum('amount', filter=Q(direction='income')),
            expense=Sum('amount', filter=Q(direction='expense'))
        )
        
        income = points_stats['income'] or 0
        expense = points_stats['expense'] or 0
        total_points = income - expense
        
        # 判断今日是否已领积分
        is_signed_in = UserPointRecord.objects.filter(user=user, type='checkin', create_time__date=today).exists()
        
        # 判断今日是否已完成记账任务
        is_bill_task_done = UserPointRecord.objects.filter(
            user=user, 
            type='task', 
            description='每日记账奖励',
            create_time__date=today
        ).exists()
        
        # 计算基于积分流水的连续签到天数（只统计到今天）
        streak_days = 0
        last_record = UserPointRecord.objects.filter(
            user=user, 
            type='checkin', 
            create_time__date__lte=today
        ).order_by('-create_time').first()
        
        if last_record:
            last_date = last_record.create_time.date()
            if last_date == today or last_date == yesterday:
                streak_days = 1
                # 往前推算，排除今天的数据，只看今天之前的记录
                records = UserPointRecord.objects.filter(
                    user=user, 
                    type='checkin', 
                    create_time__date__lt=last_date
                ).order_by('-create_time')[:10]
                current_date = last_date - timedelta(days=1)
                for rec in records:
                    if rec.create_time.date() == current_date:
                        streak_days += 1
                        current_date -= timedelta(days=1)
                    else:
                        break
        
        return HttpResult.success_with_data("获取积分成功", {
            "totalPoints": total_points,
            "continuousCheckIn": streak_days, # 这里返回基于积分流水的连续天数
            "isSignedToday": is_signed_in,
            "isBillTaskDone": is_bill_task_done
        })

class GetUserStatsView(APIView):
    """获取用户统计数据（连续打卡、连续记账、总笔数）"""
    def get(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败")
            
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        checkin_dates = UserCheckIn.objects.filter(
            user=user, 
            date__lte=today
        ).order_by('-date').values_list('date', flat=True)
        
        continuous_checkin = 0
        if checkin_dates:
            # 判断最后一次打卡是否是今天或昨天
            if checkin_dates[0] == today or checkin_dates[0] == yesterday:
                continuous_checkin = 1
                current_date = checkin_dates[0]
                for i in range(1, len(checkin_dates)):
                    if (current_date - checkin_dates[i]).days == 1:
                        continuous_checkin += 1
                        current_date = checkin_dates[i]
                    else:
                        break
        # 2. 记账总笔数
        total_records = TransactionRecord.objects.filter(user=user).count()
        # 3. 记账总天数 (第一笔账到最后一笔账的天数差)
        # 获取用户最早和最晚的记账日期
        accounting_range = TransactionRecord.objects.filter(user=user).aggregate(
            first_day=Min('date'),
            last_day=Max('date')
        )
        
        total_accounting_days = 0
        if accounting_range['first_day'] and accounting_range['last_day']:
            # 天数差 + 1 (包含头尾)
            total_accounting_days = (accounting_range['last_day'] - accounting_range['first_day']).days + 1
                
        return HttpResult.success_with_data("获取统计成功", {
            "continuousCheckIn": continuous_checkin,
            "totalAccountingDays": total_accounting_days,
            "totalRecords": total_records,
            "isCheckedIn": UserCheckIn.objects.filter(user=user, date=today).exists()
        })
