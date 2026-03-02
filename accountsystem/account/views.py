from rest_framework.views import APIView
from .models import TransactionIcon, TransactionCategory, TransactionRecord
from user.models import User
from user.utils.jwt_token import verify_token
from common.response_web import HttpResult
from common.utils import parse_date, format_datetime, format_date
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, timedelta

class GetIconsView(APIView):
    """获取所有图标列表"""
    def get(self, request, format=None):
        # 按照 group 分组或者直接全部返回
        icons = TransactionIcon.objects.all().values('id', 'name', 'icon', 'group', 'type')
        
        # 转换为列表
        icon_list = list(icons)
        
        return HttpResult.success_with_data("获取图标成功", icon_list)

from user.utils.user import get_current_user

class SaveBillView(APIView):
    """保存账单"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
        data = request.data
        amount = data.get('amount')
        bill_type = data.get('type')
        icon_id = data.get('icon_id')
        date_str = data.get('date')
        location = data.get('location', '')
        remark = data.get('remark', '')

        if not amount:
            return HttpResult.fail("请输入金额")
        if not bill_type:
            return HttpResult.fail("请选择账单类型")
        if not icon_id:
            return HttpResult.fail("请选择分类图标")
        if not date_str:
            return HttpResult.fail("请选择日期")

        # 2. 业务逻辑处理
        try:
            # 验证图标是否存在
            try:
                icon = TransactionIcon.objects.get(id=icon_id)
            except TransactionIcon.DoesNotExist:
                return HttpResult.fail("所选图标不存在")
            category, created = TransactionCategory.objects.get_or_create(
                user=user,
                name=icon.name,
                type=bill_type,
                icon=icon
            )
            
            # 更新该分类的账单笔数和更新时间
            category.count += 1
            category.save()

            # 使用公共方法解析日期
            obs_date = parse_date(date_str)

            # 创建账单记录 (TransactionRecord)
            record = TransactionRecord.objects.create(
                user=user,
                category=category,
                amount=amount,
                type=bill_type,
                date=obs_date,
                time=(timezone.now() + timezone.timedelta(hours=8)).time(), # 同样加8小时
                location=location,
                remark=remark
            )

            return HttpResult.success_with_data("保存成功", {"id": record.id})

        except Exception as e:
            print(f"保存账单异常: {str(e)}")
            return HttpResult.fail(f"保存失败: {str(e)}")

class GetBillListView(APIView):
    """获取账单列表 (按日期分组)"""
    def get(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")

        # 1. 查询该用户的所有账单记录，按日期倒序
        records = TransactionRecord.objects.filter(user=user).select_related('category', 'category__icon').order_by('-date', '-create_time')

        # 2. 格式化数据并按日期分组
        # 前端需要的格式: [{ date: '...', totalExpense: '...', items: [...] }]
        grouped_data = []
        date_map = {} # 用于快速查找日期索引

        for record in records:
            date_str = format_date(record.date)
            # 转换日期显示格式，例如: "3月2日 星期一"
            weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
            weekday_str = weekdays[record.date.weekday()]
            display_date = f"{record.date.strftime('%m月%d日')} {weekday_str}"
            
            if date_str not in date_map:
                date_group = {
                    'id': len(grouped_data) + 1,
                    'date': display_date,
                    'date_raw': date_str,
                    'totalExpense': 0,
                    'items': []
                }
                date_map[date_str] = len(grouped_data)
                grouped_data.append(date_group)
            
            idx = date_map[date_str]
            
            # 构造单条账单项
            item = {
                'id': record.id,
                'title': record.category.name,
                'amount': f"-{record.amount}" if record.type == 'expense' else f"+{record.amount}",
                'amount_value': float(record.amount),
                'type': record.type,
                'time': record.time.strftime('%H:%M'),
                'location': record.location or '',
                'remark': record.remark or '',
                'icon': record.category.icon.icon,
                'icon_id': record.category.icon.id, # 返回图标 ID 用于前端计算颜色
            }
            
            grouped_data[idx]['items'].append(item)
            if record.type == 'expense':
                grouped_data[idx]['totalExpense'] += float(record.amount)

        # 格式化总支出金额
        for group in grouped_data:
            group['totalExpense'] = f"{group['totalExpense']:.2f}"

        return HttpResult.success_with_data("获取账单成功", grouped_data)

class DeleteBillView(APIView):
    """删除账单"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
        
        bill_id = request.data.get('id')
        if not bill_id:
            return HttpResult.fail("账单 ID 不能为空")
            
        try:
            record = TransactionRecord.objects.get(id=bill_id, user=user)
            category = record.category
            
            # 删除记录
            record.delete()
            
            # 更新分类计数
            if category.count > 0:
                category.count -= 1
                category.save()
                
            return HttpResult.success("删除成功")
        except TransactionRecord.DoesNotExist:
            return HttpResult.fail("账单不存在或无权删除")
        except Exception as e:
            return HttpResult.fail(f"删除失败: {str(e)}")
