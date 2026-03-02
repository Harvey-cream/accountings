from rest_framework.views import APIView
from .models import TransactionIcon, TransactionCategory, TransactionRecord
from user.models import User
from user.utils.jwt_token import verify_token
from common.response_web import HttpResult
from django.utils import timezone
from datetime import datetime

class GetIconsView(APIView):
    """获取所有图标列表"""
    def get(self, request, format=None):
        # 按照 group 分组或者直接全部返回
        icons = TransactionIcon.objects.all().values('id', 'name', 'icon', 'group', 'type')
        
        # 转换为列表
        icon_list = list(icons)
        
        return HttpResult.success_with_data("获取图标成功", icon_list)

class SaveBillView(APIView):
    """保存账单"""
    def post(self, request, format=None):
        # 此时身份已由中间件注入到 request.user
        user = request.user

        # 1. 获取并校验数据 (逐个非空校验)
        data = request.data
        amount = data.get('amount')
        bill_type = data.get('type')
        icon_id = data.get('icon_id')
        date_str = data.get('date')
        location = data.get('location', '')
        remark = data.get('remark', '')

        if not amount:
            return HttpResult.error("请输入金额")
        if not bill_type:
            return HttpResult.error("请选择账单类型")
        if not icon_id:
            return HttpResult.error("请选择分类图标")
        if not date_str:
            return HttpResult.error("请选择日期")

        # 2. 业务逻辑处理
        try:
            # 验证图标是否存在
            try:
                icon = TransactionIcon.objects.get(id=icon_id)
            except TransactionIcon.DoesNotExist:
                return HttpResult.error("所选图标不存在")

            # 处理分类 (TransactionCategory)
            # 逻辑：如果当前用户下已存在同名且同图标的分类，则复用；否则创建
            category, created = TransactionCategory.objects.get_or_create(
                user=user,
                name=icon.name,
                type=bill_type,
                icon=icon
            )

            # 解析日期
            try:
                if '/' in date_str:
                    # 处理 M/D/YYYY
                    obs_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                else:
                    # 处理 YYYY-MM-DD
                    obs_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except Exception:
                obs_date = timezone.now().date()

            # 创建账单记录 (TransactionRecord)
            record = TransactionRecord.objects.create(
                user=user,
                category=category,
                amount=amount,
                type=bill_type,
                date=obs_date,
                time=timezone.now().time(), # 使用当前时间
                location=location,
                remark=remark
            )

            return HttpResult.success_with_data("保存成功", {"id": record.id})

        except Exception as e:
            print(f"保存账单异常: {str(e)}")
            return HttpResult.error(f"保存失败: {str(e)}")
