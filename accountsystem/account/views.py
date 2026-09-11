from rest_framework.views import APIView
from rest_framework.renderers import BaseRenderer
import json
from decimal import Decimal
from .models import TransactionIcon, TransactionCategory, TransactionRecord, TransactionBudget, AssetIcon, AssetAccount, TransactionInvoice, LangchainChatMessage
from .serializers import LangchainChatMessageSerializer
from django.http import StreamingHttpResponse
from .ai.gateway.agent import astream_accounting
from .ai.llm.response import chat, to_api_dict
from common.initia import NORMAL_ICONS
from user.models import User, UserPointRecord
from user.utils.jwt_token import verify_token
from common.response_web import HttpResult
from common.utils import parse_date, format_datetime, format_date
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from datetime import datetime, timedelta
from .services.langchain_chat import (
    create_ai_chat_messages,
    create_user_chat_message,
    parse_confirm_payload,
    resolve_confirm_card,
)
from .ai.llm.schemas import AGENT_ERROR_REPLY

class GetIconsView(APIView):
    """获取所有图标列表"""
    def get(self, request, format=None):
        # 按照 group 分组或者直接全部返回
        icons = TransactionIcon.objects.all().values('id', 'name', 'icon', 'group', 'type')
        
        # 转换为列表
        icon_list = list(icons)
        
        return HttpResult.success_with_data("获取图标成功", icon_list)

from user.utils.user_utils import get_current_user

from django.db import transaction

class SaveBillView(APIView):
    """保存或更新账单"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
        data = request.data
        bill_id = data.get('id') # 增加对 ID 的判断，用于更新
        amount = data.get('amount')
        bill_type = data.get('type')
        icon_id = data.get('icon_id')
        date_str = data.get('date')
        location = data.get('location', '')
        remark = data.get('remark', '')

        if not amount:
            return HttpResult.fail("请输入金额")
        
        try:
            amount = Decimal(str(amount))
        except Exception:
            return HttpResult.fail("金额格式错误")
        
        if not bill_type:
            return HttpResult.fail("请选择账单类型")
        if not date_str:
            return HttpResult.fail("请选择日期")

        # 2. 业务逻辑处理
        try:
            with transaction.atomic():
                obs_date = parse_date(date_str)
                
                if bill_id:
                    # --- 更新逻辑 ---
                    try:
                        record = TransactionRecord.objects.get(id=bill_id, user=user)
                        record.amount = amount
                        record.type = bill_type
                        record.date = obs_date
                        record.remark = remark
                        # 如果传了 icon_id，则尝试更新分类
                        if icon_id:
                            try:
                                icon = TransactionIcon.objects.get(id=icon_id)
                                category_name = icon.name if icon.name else "其他"
                                category, _ = TransactionCategory.objects.get_or_create(
                                    user=user, name=category_name, type=bill_type, icon=icon
                                )
                                record.category = category
                            except TransactionIcon.DoesNotExist:
                                pass
                        record.save()
                        return HttpResult.success("修改成功")
                    except TransactionRecord.DoesNotExist:
                        return HttpResult.fail("账单不存在或无权修改")
                else:
                    # --- 新增逻辑 ---
                    if not icon_id:
                        return HttpResult.fail("请选择分类图标")
                    
                    try:
                        icon = TransactionIcon.objects.get(id=icon_id)
                    except TransactionIcon.DoesNotExist:
                        return HttpResult.fail("所选图标不存在")
                    
                    category_name = icon.name if icon.name else "其他"
                    category, created = TransactionCategory.objects.get_or_create(
                        user=user,
                        name=category_name,
                        type=bill_type,
                        icon=icon
                    )
                    category.count += 1
                    category.save()
                    
                    record = TransactionRecord.objects.create(
                        user=user,
                        category=category,
                        amount=amount,
                        type=bill_type,
                        date=obs_date,
                        time=(timezone.now() + timezone.timedelta(hours=8)).time(),
                        location=location,
                        remark=remark
                    )

                    # 3. 积分逻辑
                    today = timezone.now().date()
                    has_pointed_today = UserPointRecord.objects.filter(
                        user=user, type='task', description='每日记账奖励', create_time__date=today
                    ).exists()

                    points_earned = 0
                    if not has_pointed_today:
                        UserPointRecord.objects.create(
                            user=user, amount=5, direction='income', type='task', description='每日记账奖励'
                        )
                        points_earned = 5

                    return HttpResult.success_with_data("保存成功", {
                        "id": record.id,
                        "points_earned": points_earned
                    })

        except Exception as e:
            print(f"保存账单异常: {str(e)}")
            return HttpResult.fail(f"保存失败: {str(e)}")

class GetBillListView(APIView):
    """获取账单列表 (按日期分组)"""
    def get(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")

        # 1. 获取过滤参数
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        # 2. 构建查询条件
        query = TransactionRecord.objects.filter(user=user)
        if year:
            query = query.filter(date__year=year)
        if month:
            query = query.filter(date__month=month)

        # 3. 查询并排序
        records = query.select_related('category', 'category__icon').order_by('-date', '-create_time')

        # 4. 格式化数据并按日期分组
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
                    'totalExpense': Decimal('0'),
                    'totalIncome': Decimal('0'),
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
                grouped_data[idx]['totalExpense'] += Decimal(str(record.amount))
            else:
                grouped_data[idx]['totalIncome'] += Decimal(str(record.amount))

        # 格式化金额
        for group in grouped_data:
            group['totalExpense'] = f"{float(group['totalExpense']):.2f}"
            group['totalIncome'] = f"{float(group['totalIncome']):.2f}"

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
            
            # --- 同步逻辑：如果是从 AI 对话生成的，则同步删除对话框中的卡片 ---
            LangchainChatMessage.objects.filter(record=record).delete()
            
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

class GetBillSummaryView(APIView):
    """获取账单汇总统计数据"""
    def get(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
            
        # 基础参数获取
        now = timezone.now()
        year_param = request.query_params.get('year', str(now.year))
        period = request.query_params.get('period', 'month') # week, month, year
        bill_type = request.query_params.get('type', 'expense') # expense, income
        
        # 1. 基础统计 (原有逻辑保留)
        total_income = TransactionRecord.objects.filter(user=user, type='income').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        total_expense = TransactionRecord.objects.filter(user=user, type='expense').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        total_summary = {
            'balance': f"{float(total_income - total_expense):,.2f}",
            'income': f"{float(total_income):,.2f}",
            'expense': f"{float(total_expense):,.2f}"
        }
        
        year_income = TransactionRecord.objects.filter(user=user, type='income', date__year=year_param).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        year_expense = TransactionRecord.objects.filter(user=user, type='expense', date__year=year_param).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        year_summary = {
            'balance': f"{float(year_income - year_expense):,.2f}",
            'income': f"{float(year_income):,.2f}",
            'expense': f"{float(year_expense):,.2f}"
        }
        
        # 2. 分类统计 (用于排行榜)
        # 根据 period 确定时间范围
        category_query = TransactionRecord.objects.filter(user=user, type=bill_type)
        if period == 'month':
            category_query = category_query.filter(date__year=now.year, date__month=now.month)
        elif period == 'week':
            # 最近 7 天 (包含今天)
            week_start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            category_query = category_query.filter(date__gte=week_start)
        elif period == 'year':
            category_query = category_query.filter(date__year=year_param)

        total_amount = category_query.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        category_stats = category_query.values('category__name', 'category__icon__icon', 'category__icon__id') \
            .annotate(amount=Sum('amount')) \
            .order_by('-amount')

        formatted_category_stats = []
        for stat in category_stats:
            amount = stat['amount']
            percent = (amount / total_amount * 100) if total_amount > 0 else Decimal('0')
            formatted_category_stats.append({
                'id': stat['category__icon__id'],
                'name': stat['category__name'],
                'amount': f"{'-' if bill_type == 'expense' else '+'}¥ {float(amount):,.2f}",
                'amount_value': float(amount),
                'percent': round(float(percent), 1),
                'icon': stat['category__icon__icon'],
                'icon_id': stat['category__icon__id']
            })

        # 3. 趋势图数据
        chart_labels = []
        chart_values = []
        
        if period == 'week':
            # 最近 7 天
            for i in range(6, -1, -1):
                day = now - timedelta(days=i)
                label = day.strftime('%m-%d')
                val = TransactionRecord.objects.filter(user=user, type=bill_type, date=day.date()).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                chart_labels.append(label)
                chart_values.append(val)
        elif period == 'month':
            # 本月每天
            import calendar
            _, last_day = calendar.monthrange(now.year, now.month)
            for d in range(1, last_day + 1):
                label = f"{d:02d}"
                val = TransactionRecord.objects.filter(user=user, type=bill_type, date__year=now.year, date__month=now.month, date__day=d).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                chart_labels.append(label)
                chart_values.append(val)
        elif period == 'year':
            # 全年每月
            for m in range(1, 13):
                label = f"{m}月"
                val = TransactionRecord.objects.filter(user=user, type=bill_type, date__year=year_param, date__month=m).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                chart_labels.append(label)
                chart_values.append(val)

        # 计算均值
        avg_value = sum(chart_values) / len(chart_values) if chart_values else Decimal('0')

        # 获取月度明细
        month_stats = TransactionRecord.objects.filter(user=user, date__year=year_param) \
            .annotate(month=ExtractMonth('date')) \
            .values('month', 'type') \
            .annotate(total=Sum('amount')) \
            .order_by('-month')

        month_bills_dict = {}
        for stat in month_stats:
            m = str(stat['month'])
            if m not in month_bills_dict:
                month_bills_dict[m] = {'month': m, 'income': Decimal('0'), 'expense': Decimal('0')}
            if stat['type'] == 'income':
                month_bills_dict[m]['income'] = stat['total']
            else:
                month_bills_dict[m]['expense'] = stat['total']

        month_bills = []
        for m in range(12, 0, -1):
            m_str = str(m)
            if m_str in month_bills_dict:
                item = month_bills_dict[m_str]
                item['balance'] = f"{float(item['income'] - item['expense']):,.2f}"
                item['income'] = f"{float(item['income']):,.2f}"
                item['expense'] = f"{float(item['expense']):,.2f}"
                month_bills.append(item)
        
        # 获取年度明细
        year_stats = TransactionRecord.objects.filter(user=user) \
            .annotate(year=ExtractYear('date')) \
            .values('year', 'type') \
            .annotate(total=Sum('amount')) \
            .order_by('-year')

        year_bills_dict = {}
        for stat in year_stats:
            y = str(stat['year'])
            if y not in year_bills_dict:
                year_bills_dict[y] = {'year': y, 'income': Decimal('0'), 'expense': Decimal('0')}
            if stat['type'] == 'income':
                year_bills_dict[y]['income'] = stat['total']
            else:
                year_bills_dict[y]['expense'] = stat['total']

        year_bills = []
        for y in sorted(year_bills_dict.keys(), key=int, reverse=True):
            item = year_bills_dict[y]
            item['balance'] = f"{float(item['income'] - item['expense']):,.2f}"
            item['income'] = f"{float(item['income']):,.2f}"
            item['expense'] = f"{float(item['expense']):,.2f}"
            year_bills.append(item)
            
        data = {
            'totalSummary': total_summary,
            'yearSummary': year_summary,
            'monthBills': month_bills,
            'yearBills': year_bills,
            'categoryStats': formatted_category_stats,
            'chartData': {
                'labels': chart_labels,
                'values': [float(v) for v in chart_values],
                'total': f"¥ {float(sum(chart_values)):,.2f}",
                'average': f"¥ {float(avg_value):,.2f}"
            }
        }
        
        return HttpResult.success_with_data("获取汇总数据成功", data)

class SaveBudgetView(APIView):
    """保存或更新预算"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
            
        data = request.data
        amount = data.get('amount')
        budget_type = data.get('budget_type', 'month') # 'month' 或 'year'
        period = data.get('period') # "2024-03" 或 "2024"
        is_total = data.get('is_total', False)
        icon_id = data.get('icon_id') # 仅在 is_total 为 False 时有效

        if not amount:
            return HttpResult.fail("请输入预算金额")
        if not period:
            return HttpResult.fail("请输入预算周期")

        try:
            amount = Decimal(str(amount))
            category = None
            year_period = period[:4] if budget_type == 'month' else period

            # 1. 获取对应的年总预算 (用于约束判断)
            ytb_obj = TransactionBudget.objects.filter(
                user=user, budget_type='year', period=year_period, is_total=True
            ).first()
            ytb_amount = ytb_obj.amount if ytb_obj else Decimal('0')

            if not is_total:
                # 分类预算
                if not icon_id:
                    return HttpResult.fail("请选择分类图标")
                try:
                    icon = TransactionIcon.objects.get(id=icon_id)
                    category, _ = TransactionCategory.objects.get_or_create(
                        user=user, name=icon.name, type='expense', icon=icon
                    )
                except TransactionIcon.DoesNotExist:
                    return HttpResult.fail("分类图标不存在")

                if budget_type == 'month':
                    # A. 月度分类预算约束：Sum(本月所有分类预算) <= 本月总预算
                    mtb_obj = TransactionBudget.objects.filter(
                        user=user, budget_type='month', period=period, is_total=True
                    ).first()
                    if not mtb_obj:
                        return HttpResult.fail("请先设置本月总预算")
                    
                    other_mcb_sum = TransactionBudget.objects.filter(
                        user=user, budget_type='month', period=period, is_total=False
                    ).exclude(category=category).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                    
                    if (other_mcb_sum + amount) > mtb_obj.amount:
                        return HttpResult.fail(f"本月分类预算总额({other_mcb_sum + amount})不能超过月总预算({mtb_obj.amount})")

                    # B. 自动同步：如果年预算中没有这个分类，自动创建一个 (数据一致)
                    ycb_obj, created = TransactionBudget.objects.get_or_create(
                        user=user, budget_type='year', period=year_period, is_total=False, category=category,
                        defaults={'amount': amount}
                    )
                    # 如果已经存在，我们不自动修改年分类预算金额，因为“用户可以修改年预算”
                else:
                    # 年度分类预算约束：Sum(本年所有分类预算) <= 年总预算
                    if not ytb_obj:
                        return HttpResult.fail("请先设置年度总预算")
                    
                    other_ycb_sum = TransactionBudget.objects.filter(
                        user=user, budget_type='year', period=year_period, is_total=False
                    ).exclude(category=category).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                    
                    if (other_ycb_sum + amount) > ytb_amount:
                        return HttpResult.fail(f"年度分类预算总额({other_ycb_sum + amount})不能超过年总预算({ytb_amount})")
            else:
                # 总预算
                if budget_type == 'month':
                    # 月总预算约束：Sum(本年所有月份的总预算) <= 年总预算
                    if not ytb_obj:
                        return HttpResult.fail("请先设置年度总预算")
                    
                    other_mtb_sum = TransactionBudget.objects.filter(
                        user=user, budget_type='month', period__startswith=year_period, is_total=True
                    ).exclude(period=period).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                    
                    if (other_mtb_sum + amount) > ytb_amount:
                        return HttpResult.fail(f"各月总预算之和({other_mtb_sum + amount})不能超过年总预算({ytb_amount})")
                else:
                    # 年总预算修改：必须大于等于已设置的月总预算之和
                    all_mtb_sum = TransactionBudget.objects.filter(
                        user=user, budget_type='month', period__startswith=year_period, is_total=True
                    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                    
                    if amount < all_mtb_sum:
                        return HttpResult.fail(f"年总预算({amount})不能小于已设置的月总预算之和({all_mtb_sum})")

            # 保存或更新当前记录
            budget, _ = TransactionBudget.objects.update_or_create(
                user=user, category=category, budget_type=budget_type, period=period, is_total=is_total,
                defaults={'amount': amount}
            )

            return HttpResult.success_with_data("保存预算成功", {"id": budget.id})

        except Exception as e:
            print(f"保存预算异常: {str(e)}")
            return HttpResult.fail(f"保存预算失败: {str(e)}")

class GetBudgetView(APIView):
    """获取预算概览及分类预算列表"""
    def get(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")

        budget_type = request.query_params.get('budget_type', 'month') # 'month' 或 'year'
        period = request.query_params.get('period') # "2024-03" 或 "2024"

        if not period:
            return HttpResult.fail("请提供预算周期")

        try:
            year_val = period[:4] if budget_type == 'month' else period
            
            # 1. 获取总预算
            total_budget_obj = TransactionBudget.objects.filter(
                user=user, budget_type=budget_type, period=period, is_total=True
            ).first()
            
            total_amount = Decimal('0.0')
            if total_budget_obj:
                total_amount = total_budget_obj.amount
            elif budget_type == 'year':
                # 如果没有设置年总预算，汇总所有月份的总预算作为展示值
                total_amount = TransactionBudget.objects.filter(
                    user=user, budget_type='month', period__startswith=year_val, is_total=True
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

            # 2. 获取该周期内的总支出
            record_query = TransactionRecord.objects.filter(user=user, type='expense')
            if budget_type == 'month':
                y, m = period.split('-')
                record_query = record_query.filter(date__year=y, date__month=m)
            else:
                record_query = record_query.filter(date__year=year_val)
            
            total_spent = record_query.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

            # 3. 获取分类预算列表
            # 获取当前周期下所有的分类预算记录
            budget_records = TransactionBudget.objects.filter(
                user=user, budget_type=budget_type, period=period, is_total=False
            ).select_related('category', 'category__icon')

            # 如果是年视图，还需要找出那些“只在月度设置了预算但年度还没设置”的分类
            category_list = []
            seen_categories = set()

            for br in budget_records:
                cat_record_query = record_query.filter(category=br.category)
                cat_spent = cat_record_query.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')
                
                amount = br.amount
                # 年视图下，如果用户没有手动修改过（或者我们想展示汇总），可以这里处理
                # 但根据 SaveBudgetView 的同步逻辑，已经存在了。
                
                percent = round(float(cat_spent / amount * 100), 1) if amount > 0 else 0
                
                category_list.append({
                    'id': br.id,
                    'name': br.category.name,
                    'icon': br.category.icon.icon,
                    'icon_id': br.category.icon.id,
                    'amount': float(amount),
                    'spent': float(cat_spent),
                    'percent': min(percent, 100)
                })
                seen_categories.add(br.category_id)

            # 年视图特有：自动汇总月度分类预算到年度显示中（如果年度还没这条记录）
            if budget_type == 'year':
                monthly_categories = TransactionBudget.objects.filter(
                    user=user, budget_type='month', period__startswith=year_val, is_total=False
                ).exclude(category_id__in=seen_categories).values('category').annotate(total_amount=Sum('amount'))
                
                for item in monthly_categories:
                    cat = TransactionCategory.objects.select_related('icon').get(id=item['category'])
                    cat_record_query = record_query.filter(category=cat)
                    cat_spent = cat_record_query.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')
                    
                    amount = item['total_amount']
                    percent = round(float(cat_spent / amount * 100), 1) if amount > 0 else 0
                    
                    category_list.append({
                        'id': f"temp_{cat.id}",
                        'name': cat.name,
                        'icon': cat.icon.icon,
                        'icon_id': cat.icon.id,
                        'amount': float(amount),
                        'spent': float(cat_spent),
                        'percent': min(percent, 100)
                    })

            data = {
                'totalAmount': float(total_amount),
                'totalSpent': float(total_spent),
                'categories': category_list
            }

            return HttpResult.success_with_data("获取预算数据成功", data)

        except Exception as e:
            print(f"获取预算异常: {str(e)}")
            return HttpResult.fail(f"获取预算失败: {str(e)}")


_CONFIRM_DONE_REPLY = "这条确认已经处理过啦～"


def _chat_turn_user_message(user, content):
    """校验并保存用户消息，失败时返回 (None, error_response)。"""
    if not content:
        return None, HttpResult.fail("消息内容不能为空")
    return create_user_chat_message(user, content), None


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class LangchainChatView(APIView):
    """AI 记账对话接口"""
    def get(self, request):
        """获取历史对话记录"""
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")
        
        # 过滤出该用户的所有对话，且如果消息关联了账单记录，则要求该记录必须存在
        # 这确保了如果在其他地方删除了账单，对话中的卡片也会同步消失（因为 get 会根据外键 record 过滤）
        limit = min(max(int(request.query_params.get('limit', 20)), 1), 50)
        before_id = request.query_params.get('before_id')

        qs = LangchainChatMessage.objects.filter(user=user).order_by('-create_time')
        if before_id:
            try:
                qs = qs.filter(id__lt=int(before_id))
            except (TypeError, ValueError):
                pass

        batch = list(qs[: limit + 1])
        has_more = len(batch) > limit
        batch = batch[:limit]
        batch.reverse()

        serializer = LangchainChatMessageSerializer(batch, many=True)
        final_data = [m for m in serializer.data if m is not None]
        return HttpResult.success_with_data("获取成功", {"messages": final_data, "has_more": has_more})


class LangchainChatStreamView(APIView):
    """AI 记账对话流式接口（SSE，H5）"""

    class _SSERenderer(BaseRenderer):
        media_type = "text/event-stream"
        format = "event-stream"
        charset = "utf-8"

        def render(self, data, accepted_media_type=None, renderer_context=None):
            return data

    renderer_classes = [_SSERenderer]

    def finalize_response(self, request, response, *args, **kwargs):
        if isinstance(response, StreamingHttpResponse):
            return response
        return super().finalize_response(request, response, *args, **kwargs)

    def post(self, request):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户未登录")

        content = request.data.get("content")
        confirm = parse_confirm_payload(request.data)
        if confirm is None and "confirm" in (request.data or {}):
            return HttpResult.fail("确认参数无效")
        confirm_extra = None
        if confirm is not None:
            ok, confirm_extra = resolve_confirm_card(user, confirm.get("message_id"))
            if not ok:
                # 走 SSE 契约返回，否则前端 fetch 拿到非流式响应会一直等不到 done
                return StreamingHttpResponse(
                    iter([_sse({"type": "error", "message": _CONFIRM_DONE_REPLY})]),
                    content_type="text/event-stream; charset=utf-8",
                )
            if confirm_extra:
                confirm["confirm_extra"] = confirm_extra
        if confirm is not None and not content:
            content = "确认" if confirm.get("confirm") else "取消"
        user_msg, err = _chat_turn_user_message(user, content)
        if err:
            return err

        def generate():
            import asyncio

            yield _sse({"type": "status", "text": "鸭鸭正在想..."})
            yield ":" + (" " * 2048) + "\n\n"

            loop = asyncio.new_event_loop()
            ai_data = None
            try:
                agen = astream_accounting(content, user=user, confirm=confirm)
                while True:
                    try:
                        event = loop.run_until_complete(agen.__anext__())
                    except StopAsyncIteration:
                        break

                    if event.get("type") == "agent_result":
                        ai_data = to_api_dict(event["data"])
                        continue
                    if event.get("type") == "error":
                        ai_data = chat(event.get("message", ""))
                        if event.get("remark"):
                            ai_data["remark"] = event["remark"]
                        yield _sse(event)
                        break
                    yield _sse(event)
            except Exception as e:
                print(f"流式对话异常: {e}")
                ai_data = chat(AGENT_ERROR_REPLY)
                yield _sse({"type": "error", "message": ai_data.get("reply", "")})
            finally:
                loop.close()

            if ai_data is None:
                ai_data = chat(AGENT_ERROR_REPLY)
            ai_msgs = create_ai_chat_messages(user, content, ai_data)
            serializer = LangchainChatMessageSerializer([user_msg, *ai_msgs], many=True)
            yield _sse({"type": "done", "code": 0, "data": serializer.data})

        response = StreamingHttpResponse(generate(), content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response

class SaveAssetAccountView(APIView):
    """保存或更新资产账户"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
            
        data = request.data
        account_id = data.get('id') # 如果有 ID 则为更新，没有则为新增
        name = data.get('name')
        asset_type_id = data.get('asset_type_id')
        balance = data.get('balance', 0)
        account_type = data.get('type', 'asset') # asset 或 debt
        is_included_in_total = data.get('is_included_in_total', True)
        remark = data.get('remark', '')

        if not name:
            return HttpResult.fail("请输入账户名称")
        if not asset_type_id:
            return HttpResult.fail("请选择资产类型")

        try:
            balance = Decimal(str(balance))
            
            # 1. 验证资产类型图标是否存在
            try:
                asset_icon = AssetIcon.objects.get(id=asset_type_id)
            except AssetIcon.DoesNotExist:
                return HttpResult.fail("所选资产类型不存在")

            # 2. 保存或更新
            if account_id:
                # 更新逻辑
                try:
                    account = AssetAccount.objects.get(id=account_id, user=user)
                    account.name = name
                    account.asset_type = asset_icon
                    account.balance = balance
                    account.type = account_type
                    account.is_included_in_total = is_included_in_total
                    account.remark = remark
                    account.save()
                except AssetAccount.DoesNotExist:
                    return HttpResult.fail("账户不存在或无权修改")
            else:
                # 新增逻辑
                account = AssetAccount.objects.create(
                    user=user,
                    name=name,
                    asset_type=asset_icon,
                    balance=balance,
                    type=account_type,
                    is_included_in_total=is_included_in_total,
                    remark=remark
                )

            return HttpResult.success_with_data("保存成功", {"id": account.id})

        except Exception as e:
            print(f"保存资产账户异常: {str(e)}")
            return HttpResult.fail(f"保存失败: {str(e)}")

class GetAssetListView(APIView):
    """获取资产账户列表"""
    def get(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")

        try:
            # 1. 查询用户的所有资产账户
            accounts = AssetAccount.objects.filter(user=user).select_related('asset_type').order_by('type', 'create_time')

            # 2. 按图标名称（大类）进行分组
            # 前端需要的格式: [{ name: '储蓄卡', total: '...', items: [...] }]
            grouped_dict = {}
            
            total_asset = Decimal('0')
            total_debt = Decimal('0')

            for acc in accounts:
                # 确定分组名称 (使用资产图标的名称作为组名，如：现金、储蓄卡)
                group_name = acc.asset_type.name
                if acc.type == 'debt' and group_name != '负债':
                    group_name = '负债' # 统一将负债类的放入负债组，或者保持原图标名

                if group_name not in grouped_dict:
                    grouped_dict[group_name] = {
                        'name': group_name,
                        'total': Decimal('0'),
                        'items': []
                    }
                
                # 格式化单条数据
                amount = acc.balance
                if acc.type == 'debt':
                    # 负债显示为负数
                    display_amount = -abs(amount)
                    total_debt += abs(amount)
                else:
                    display_amount = abs(amount)
                    total_asset += abs(amount)

                item = {
                    'id': acc.id,
                    'name': acc.name,
                    'amount': f"{display_amount:.2f}",
                    'icon': acc.asset_type.icon,
                    'iconColor': '#fff',
                    'bgClass': acc.asset_type.bg_class,
                    'remark': acc.remark or '',
                    'type': acc.type
                }
                
                grouped_dict[group_name]['items'].append(item)
                grouped_dict[group_name]['total'] += display_amount

            # 3. 转换为列表并格式化金额
            asset_groups = []
            for group in grouped_dict.values():
                group['total'] = f"{group['total']:.2f}"
                asset_groups.append(group)

            # 计算汇总数据
            net_asset = total_asset - total_debt
            
            data = {
                'groups': asset_groups,
                'summary': {
                    'total_asset': f"{total_asset:.2f}",
                    'total_debt': f"{total_debt:.2f}",
                    'net_asset': f"{net_asset:.2f}"
                }
            }

            return HttpResult.success_with_data("获取资产列表成功", data)

        except Exception as e:
            print(f"获取资产列表异常: {str(e)}")
            return HttpResult.fail(f"获取失败: {str(e)}")

class SaveInvoiceView(APIView):
    """保存或更新发票"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
        data = request.data
        invoice_id = data.get('id')
        name = data.get('name')
        tax_id = data.get('taxId') # 对应前端字段名
        amount = data.get('amount', 0)
        address = data.get('address', '')
        phone = data.get('phone', '')
        bank = data.get('bank', '')
        account = data.get('account', '')
        remark = data.get('remark', '')

        if not name:
            return HttpResult.fail("请输入发票抬头名称")
        if not tax_id:
            return HttpResult.fail("请输入税号")

        try:
            amount = Decimal(str(amount))
            
            if invoice_id:
                # 更新
                try:
                    invoice = TransactionInvoice.objects.get(id=invoice_id, user=user)
                    invoice.name = name
                    invoice.tax_id = tax_id
                    invoice.amount = amount
                    invoice.address = address
                    invoice.phone = phone
                    invoice.bank = bank
                    invoice.account = account
                    invoice.remark = remark
                    invoice.save()
                except TransactionInvoice.DoesNotExist:
                    return HttpResult.fail("发票信息不存在或无权修改")
            else:
                # 新增
                invoice = TransactionInvoice.objects.create(
                    user=user,
                    name=name,
                    tax_id=tax_id,
                    amount=amount,
                    address=address,
                    phone=phone,
                    bank=bank,
                    account=account,
                    remark=remark
                )

            return HttpResult.success_with_data("保存成功", {"id": invoice.id})

        except Exception as e:
            print(f"保存发票异常: {str(e)}")
            return HttpResult.fail(f"保存失败: {str(e)}")

class DeleteInvoiceView(APIView):
    """删除发票"""
    def post(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")
        
        invoice_id = request.data.get('id')
        if not invoice_id:
            return HttpResult.fail("发票 ID 不能为空")
            
        try:
            invoice = TransactionInvoice.objects.get(id=invoice_id, user=user)
            invoice.delete()
            return HttpResult.success("删除成功")
        except TransactionInvoice.DoesNotExist:
            return HttpResult.fail("发票不存在或无权删除")
        except Exception as e:
            return HttpResult.fail(f"删除失败: {str(e)}")

class GetInvoiceListView(APIView):
    """获取发票列表"""
    def get(self, request, format=None):
        user = get_current_user(request)
        if not user:
            return HttpResult.fail("用户身份校验失败，请重新登录")

        try:
            invoices = TransactionInvoice.objects.filter(user=user).order_by('-create_time')
            
            data_list = []
            for item in invoices:
                data_list.append({
                    'id': item.id,
                    'name': item.name,
                    'taxId': item.tax_id,
                    'amount': f"{float(item.amount):,.2f}",
                    'address': item.address or '',
                    'phone': item.phone or '',
                    'bank': item.bank or '',
                    'account': item.account or '',
                    'remark': item.remark or ''
                })

            return HttpResult.success_with_data("获取发票列表成功", data_list)

        except Exception as e:
            print(f"获取发票列表异常: {str(e)}")
            return HttpResult.fail(f"获取失败: {str(e)}")
