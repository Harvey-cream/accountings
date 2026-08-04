"""
AI 账单业务能力（类 MCP Tool 的能力接口）。

供未来 LangChain Tool / 现有 Agent 落库与查账复用。
不处理 HTTP、鉴权、Serializer、Agent 编排。
人用 API（View）保持独立，不强制走本模块。
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from common.initia import NORMAL_ICONS

from ..models import (
    LangchainChatMessage,
    TransactionCategory,
    TransactionIcon,
    TransactionRecord,
)
from .errors import ServiceError


def _norm_bill_type(bill_type: str) -> str:
    if bill_type in ("支出", "expense"):
        return "expense"
    if bill_type in ("收入", "income"):
        return "income"
    raise ServiceError(f"无效账单类型: {bill_type}")


def _resolve_category(user, category_name: str, bill_type: str) -> tuple[TransactionCategory, str]:
    matched = next(
        (item for item in NORMAL_ICONS if item["name"] == category_name),
        {"icon": "notes-o", "name": category_name or "其他"},
    )
    icon_code = matched.get("icon", "notes-o")
    icon_obj = TransactionIcon.objects.filter(icon=icon_code).first()
    if icon_obj is None:
        raise ServiceError(f"分类图标不存在: {icon_code}")
    cat_name = matched.get("name") or category_name or "其他"
    category, _ = TransactionCategory.objects.get_or_create(
        user=user,
        name=cat_name,
        defaults={"type": bill_type, "icon": icon_obj},
    )
    return category, icon_code


def create_expense(
    user,
    *,
    amount: Decimal | float | str,
    bill_type: str = "expense",
    category_name: str = "其他",
    remark: str = "",
    obs_date: date | None = None,
) -> dict:
    """新增一笔账单。返回 {id, type, category, amount, icon, remark, date}。"""
    try:
        money = Decimal(str(amount))
    except Exception as e:
        raise ServiceError("金额格式错误") from e
    if money <= 0:
        raise ServiceError("金额必须大于 0")

    bt = _norm_bill_type(bill_type)
    category, icon_code = _resolve_category(user, category_name, bt)
    now = timezone.now()
    record = TransactionRecord.objects.create(
        user=user,
        category=category,
        amount=money,
        type=bt,
        date=obs_date or now.date(),
        time=now.time(),
        remark=remark or "",
    )
    category.count += 1
    category.save(update_fields=["count", "update_time"])
    return {
        "id": record.id,
        "type": bt,
        "category": category.name,
        "amount": float(record.amount),
        "icon": icon_code,
        "remark": record.remark or "",
        "date": str(record.date),
    }


def update_expense(
    user,
    bill_id,
    *,
    amount: Decimal | float | str | None = None,
    bill_type: str | None = None,
    category_name: str | None = None,
    remark: str | None = None,
    obs_date: date | None = None,
) -> dict:
    """更新用户名下账单。返回更新后的摘要 dict。"""
    try:
        record = TransactionRecord.objects.select_related("category", "category__icon").get(
            id=bill_id, user=user
        )
    except TransactionRecord.DoesNotExist as e:
        raise ServiceError("账单不存在或无权修改") from e

    if amount is not None:
        try:
            money = Decimal(str(amount))
        except Exception as e:
            raise ServiceError("金额格式错误") from e
        if money <= 0:
            raise ServiceError("金额必须大于 0")
        record.amount = money

    if bill_type is not None:
        record.type = _norm_bill_type(bill_type)

    if category_name is not None:
        category, _ = _resolve_category(user, category_name, record.type)
        record.category = category

    if remark is not None:
        record.remark = remark
    if obs_date is not None:
        record.date = obs_date

    record.save()
    return {
        "id": record.id,
        "type": record.type,
        "category": record.category.name,
        "amount": float(record.amount),
        "icon": record.category.icon.icon if record.category.icon_id else "notes-o",
        "remark": record.remark or "",
        "date": str(record.date),
    }


def query_expense(
    user,
    *,
    days: int = 30,
    bill_type: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """查询近 N 天账单列表（结构化，供 AI Tool 使用）。"""
    today = date.today()
    start = today - timedelta(days=max(days, 1))
    qs = (
        TransactionRecord.objects.filter(user=user, date__gte=start, date__lte=today)
        .select_related("category", "category__icon")
        .order_by("-date", "-time", "-id")
    )
    if bill_type:
        qs = qs.filter(type=_norm_bill_type(bill_type))

    return [_record_row(r) for r in qs[: max(limit, 1)]]


def search_expense(
    user,
    *,
    keyword: str | None = None,
    category_name: str | None = None,
    days: int | None = 30,
    start_date: date | None = None,
    end_date: date | None = None,
    bill_type: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """按当前用户筛选账单（备注/分类/日期），供改单、删单前定位。不要求用户提供 id。"""
    qs = (
        TransactionRecord.objects.filter(user=user)
        .select_related("category", "category__icon")
        .order_by("-date", "-time", "-id")
    )
    today = date.today()
    if start_date or end_date:
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
    elif days is not None:
        start = today - timedelta(days=max(int(days), 1))
        qs = qs.filter(date__gte=start, date__lte=today)

    if bill_type:
        qs = qs.filter(type=_norm_bill_type(bill_type))
    if category_name:
        qs = qs.filter(category__name=category_name.strip())
    if keyword:
        qs = qs.filter(remark__icontains=keyword.strip())

    return [_record_row(r) for r in qs[: max(limit, 1)]]


def delete_expense(user, bill_id) -> dict:
    """删除当前用户名下账单；同步清理关联 AI 聊天卡片。"""
    try:
        record = TransactionRecord.objects.select_related("category").get(
            id=bill_id, user=user
        )
    except TransactionRecord.DoesNotExist as e:
        raise ServiceError("账单不存在或无权删除") from e

    snapshot = _record_row(record)
    category = record.category

    LangchainChatMessage.objects.filter(record=record).delete()
    record.delete()
    if category is not None and category.count > 0:
        category.count -= 1
        category.save(update_fields=["count", "update_time"])
    return snapshot


def _record_row(r: TransactionRecord) -> dict:
    return {
        "id": r.id,
        "type": r.type,
        "category": r.category.name if r.category_id else "其他",
        "amount": float(r.amount),
        "icon": r.category.icon.icon if r.category_id and r.category.icon_id else "notes-o",
        "remark": r.remark or "",
        "date": str(r.date),
        "time": r.time.strftime("%H:%M") if r.time else "",
    }


def _fmt_amount(v) -> str:
    try:
        n = float(v)
        if n.is_integer():
            return str(int(n))
        return ("%s" % n).rstrip("0").rstrip(".")
    except Exception:
        return str(v)


def analyze_expense(user, *, days: int = 30, category_name: str | None = None) -> str:
    """
    近 N 天收支文字摘要（笔数、总额、算式、分类），供 AI 参考。
    可选 category_name 只统计该分类。纯聚合，不含 LLM。
    """
    try:
        today = date.today()
        start = today - timedelta(days=max(days, 1))
        records = TransactionRecord.objects.filter(
            user=user, date__gte=start, date__lte=today
        ).select_related("category")
        if category_name:
            records = records.filter(category__name=category_name.strip())

        label = f"分类「{category_name}」" if category_name else ""
        if not records.exists():
            return f"最近{days}天{label}暂无账单记录。"

        expense_qs = records.filter(type="expense").order_by("date", "time", "id")
        income_qs = records.filter(type="income").order_by("date", "time", "id")

        total_expense = expense_qs.aggregate(s=Sum("amount"))["s"] or 0
        total_income = income_qs.aggregate(s=Sum("amount"))["s"] or 0

        income_amounts = list(income_qs.values_list("amount", flat=True)[:20])
        expense_amounts = list(expense_qs.values_list("amount", flat=True)[:20])

        def _formula(amounts) -> str:
            if not amounts:
                return ""
            return " + ".join(_fmt_amount(a) for a in amounts)

        income_formula = _formula(income_amounts)
        expense_formula = _formula(expense_amounts)

        cat_stats = (
            expense_qs.values("category__name").annotate(total=Sum("amount")).order_by("-total")
        )
        cat_lines = [f"  {s['category__name']}: {_fmt_amount(s['total'])}元" for s in cat_stats]

        lines = [
            f"统计周期：{start} 至 {today}",
        ]
        if category_name:
            lines.append(f"筛选分类：{category_name}")
        lines.extend(
            [
                f"收入笔数：{income_qs.count()}笔",
                f"支出笔数：{expense_qs.count()}笔",
                f"总收入：{_fmt_amount(total_income)}元",
                f"总支出：{_fmt_amount(total_expense)}元",
                f"净结余：{_fmt_amount(total_income - total_expense)}元",
                f"收入算式：{income_formula if income_formula else '无收入记录'} = {_fmt_amount(total_income)}",
                f"支出算式：{expense_formula if expense_formula else '无支出记录'} = {_fmt_amount(total_expense)}",
            ]
        )
        if cat_lines and not category_name:
            lines.append("各分类支出：")
            lines.extend(cat_lines)
        return "\n".join(lines)
    except Exception as e:
        print(f"查询账单失败: {e}")
        return "账单数据查询失败，请稍后再试。"


def _expense_total(user, start: date, end: date) -> dict:
    qs = TransactionRecord.objects.filter(user=user, date__gte=start, date__lte=end)
    expense = qs.filter(type="expense").aggregate(s=Sum("amount"))["s"] or Decimal("0")
    income = qs.filter(type="income").aggregate(s=Sum("amount"))["s"] or Decimal("0")
    return {
        "start": str(start),
        "end": str(end),
        "expense": float(expense),
        "income": float(income),
        "net": float(income - expense),
        "expense_count": qs.filter(type="expense").count(),
        "income_count": qs.filter(type="income").count(),
    }


def compare_expense(user, *, days: int = 30) -> dict:
    """对比近 N 天与上一段同等天数的收支，供趋势/对比问答。"""
    days = max(int(days), 1)
    today = date.today()
    cur_start = today - timedelta(days=days)
    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days)

    current = _expense_total(user, cur_start, today)
    previous = _expense_total(user, prev_start, prev_end)
    diff_expense = current["expense"] - previous["expense"]
    base = previous["expense"]
    pct = round(diff_expense / base * 100, 1) if base else None
    return {
        "days": days,
        "current": current,
        "previous": previous,
        "expense_diff": diff_expense,
        "expense_change_percent": pct,
    }
