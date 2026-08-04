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

from ..models import TransactionCategory, TransactionIcon, TransactionRecord
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

    rows = []
    for r in qs[: max(limit, 1)]:
        rows.append(
            {
                "id": r.id,
                "type": r.type,
                "category": r.category.name,
                "amount": float(r.amount),
                "icon": r.category.icon.icon if r.category.icon_id else "notes-o",
                "remark": r.remark or "",
                "date": str(r.date),
                "time": r.time.strftime("%H:%M") if r.time else "",
            }
        )
    return rows


def analyze_expense(user, *, days: int = 30) -> str:
    """
    近 N 天收支文字摘要（笔数、总额、算式、分类），供 AI 参考。
    纯聚合，不含 LLM。
    """
    try:
        today = date.today()
        start = today - timedelta(days=max(days, 1))
        records = TransactionRecord.objects.filter(
            user=user, date__gte=start, date__lte=today
        ).select_related("category")

        if not records.exists():
            return f"最近{days}天暂无账单记录。"

        expense_qs = records.filter(type="expense").order_by("date", "time", "id")
        income_qs = records.filter(type="income").order_by("date", "time", "id")

        total_expense = expense_qs.aggregate(s=Sum("amount"))["s"] or 0
        total_income = income_qs.aggregate(s=Sum("amount"))["s"] or 0

        income_amounts = list(income_qs.values_list("amount", flat=True)[:20])
        expense_amounts = list(expense_qs.values_list("amount", flat=True)[:20])

        def _fmt(v) -> str:
            try:
                n = float(v)
                if n.is_integer():
                    return str(int(n))
                return ("%s" % n).rstrip("0").rstrip(".")
            except Exception:
                return str(v)

        def _formula(amounts) -> str:
            if not amounts:
                return ""
            return " + ".join(_fmt(a) for a in amounts)

        income_formula = _formula(income_amounts)
        expense_formula = _formula(expense_amounts)

        cat_stats = (
            expense_qs.values("category__name").annotate(total=Sum("amount")).order_by("-total")
        )
        cat_lines = [f"  {s['category__name']}: {_fmt(s['total'])}元" for s in cat_stats]

        lines = [
            f"统计周期：{start} 至 {today}",
            f"收入笔数：{income_qs.count()}笔",
            f"支出笔数：{expense_qs.count()}笔",
            f"总收入：{_fmt(total_income)}元",
            f"总支出：{_fmt(total_expense)}元",
            f"净结余：{_fmt(total_income - total_expense)}元",
            f"收入算式：{income_formula if income_formula else '无收入记录'} = {_fmt(total_income)}",
            f"支出算式：{expense_formula if expense_formula else '无支出记录'} = {_fmt(total_expense)}",
        ]
        if cat_lines:
            lines.append("各分类支出：")
            lines.extend(cat_lines)
        return "\n".join(lines)
    except Exception as e:
        print(f"查询账单失败: {e}")
        return "账单数据查询失败，请稍后再试。"
