"""
AI 预算业务能力（类 MCP Tool 的能力接口）。

供未来 LangChain Tool 复用。不含 HTTP / 鉴权 / Agent 编排。
"""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum

from ..models import TransactionBudget, TransactionCategory, TransactionIcon, TransactionRecord
from .errors import ServiceError


def _resolve_expense_category(user, category_name: str) -> TransactionCategory:
    icon = TransactionIcon.objects.filter(name=category_name).first()
    if icon is None:
        icon = TransactionIcon.objects.filter(icon="notes-o").first()
    if icon is None:
        raise ServiceError(f"分类不存在: {category_name}")
    category, _ = TransactionCategory.objects.get_or_create(
        user=user, name=icon.name or category_name, type="expense", icon=icon
    )
    return category


def create_budget(
    user,
    *,
    amount: Decimal | float | str,
    budget_type: str = "month",
    period: str,
    is_total: bool = True,
    category_name: str | None = None,
) -> dict:
    """创建或覆盖写入预算（upsert）。返回 {id, amount, budget_type, period, is_total}。"""
    return update_budget(
        user,
        amount=amount,
        budget_type=budget_type,
        period=period,
        is_total=is_total,
        category_name=category_name,
    )


def update_budget(
    user,
    *,
    amount: Decimal | float | str,
    budget_type: str = "month",
    period: str,
    is_total: bool = True,
    category_name: str | None = None,
) -> dict:
    """
    保存/更新预算。
    约束与人用 API 对齐的核心规则：分类预算需先有总预算；月总预算需先有年总预算。
    """
    if budget_type not in ("month", "year"):
        raise ServiceError("budget_type 只能是 month 或 year")
    if not period:
        raise ServiceError("请提供预算周期")

    try:
        money = Decimal(str(amount))
    except Exception as e:
        raise ServiceError("金额格式错误") from e
    if money < 0:
        raise ServiceError("预算金额不能为负")

    category = None
    year_period = period[:4] if budget_type == "month" else period

    ytb = TransactionBudget.objects.filter(
        user=user, budget_type="year", period=year_period, is_total=True
    ).first()
    ytb_amount = ytb.amount if ytb else Decimal("0")

    if not is_total:
        if not category_name:
            raise ServiceError("分类预算需要 category_name")
        category = _resolve_expense_category(user, category_name)

        if budget_type == "month":
            mtb = TransactionBudget.objects.filter(
                user=user, budget_type="month", period=period, is_total=True
            ).first()
            if not mtb:
                raise ServiceError("请先设置本月总预算")
            other = (
                TransactionBudget.objects.filter(
                    user=user, budget_type="month", period=period, is_total=False
                )
                .exclude(category=category)
                .aggregate(Sum("amount"))["amount__sum"]
                or Decimal("0")
            )
            if other + money > mtb.amount:
                raise ServiceError(
                    f"本月分类预算总额({other + money})不能超过月总预算({mtb.amount})"
                )
            TransactionBudget.objects.get_or_create(
                user=user,
                budget_type="year",
                period=year_period,
                is_total=False,
                category=category,
                defaults={"amount": money},
            )
        else:
            if not ytb:
                raise ServiceError("请先设置年度总预算")
            other = (
                TransactionBudget.objects.filter(
                    user=user, budget_type="year", period=year_period, is_total=False
                )
                .exclude(category=category)
                .aggregate(Sum("amount"))["amount__sum"]
                or Decimal("0")
            )
            if other + money > ytb_amount:
                raise ServiceError(
                    f"年度分类预算总额({other + money})不能超过年总预算({ytb_amount})"
                )
    else:
        if budget_type == "month":
            if not ytb:
                raise ServiceError("请先设置年度总预算")
            other = (
                TransactionBudget.objects.filter(
                    user=user,
                    budget_type="month",
                    period__startswith=year_period,
                    is_total=True,
                )
                .exclude(period=period)
                .aggregate(Sum("amount"))["amount__sum"]
                or Decimal("0")
            )
            if other + money > ytb_amount:
                raise ServiceError(
                    f"各月总预算之和({other + money})不能超过年总预算({ytb_amount})"
                )
        else:
            all_mtb = (
                TransactionBudget.objects.filter(
                    user=user,
                    budget_type="month",
                    period__startswith=year_period,
                    is_total=True,
                ).aggregate(Sum("amount"))["amount__sum"]
                or Decimal("0")
            )
            if money < all_mtb:
                raise ServiceError(
                    f"年总预算({money})不能小于已设置的月总预算之和({all_mtb})"
                )

    budget, _ = TransactionBudget.objects.update_or_create(
        user=user,
        category=category,
        budget_type=budget_type,
        period=period,
        is_total=is_total,
        defaults={"amount": money},
    )
    return {
        "id": budget.id,
        "amount": float(budget.amount),
        "budget_type": budget.budget_type,
        "period": budget.period,
        "is_total": budget.is_total,
        "category": category.name if category else None,
    }


def query_budget(user, *, budget_type: str = "month", period: str) -> dict:
    """查询预算概览：总额、已花费、分类列表。"""
    if not period:
        raise ServiceError("请提供预算周期")
    if budget_type not in ("month", "year"):
        raise ServiceError("budget_type 只能是 month 或 year")

    year_val = period[:4] if budget_type == "month" else period
    total_obj = TransactionBudget.objects.filter(
        user=user, budget_type=budget_type, period=period, is_total=True
    ).first()

    total_amount = Decimal("0")
    if total_obj:
        total_amount = total_obj.amount
    elif budget_type == "year":
        total_amount = (
            TransactionBudget.objects.filter(
                user=user, budget_type="month", period__startswith=year_val, is_total=True
            ).aggregate(Sum("amount"))["amount__sum"]
            or Decimal("0")
        )

    record_qs = TransactionRecord.objects.filter(user=user, type="expense")
    if budget_type == "month":
        y, m = period.split("-")
        record_qs = record_qs.filter(date__year=y, date__month=m)
    else:
        record_qs = record_qs.filter(date__year=year_val)

    total_spent = record_qs.aggregate(Sum("amount"))["amount__sum"] or Decimal("0")

    categories = []
    for br in TransactionBudget.objects.filter(
        user=user, budget_type=budget_type, period=period, is_total=False
    ).select_related("category", "category__icon"):
        spent = (
            record_qs.filter(category=br.category).aggregate(Sum("amount"))["amount__sum"]
            or Decimal("0")
        )
        pct = round(float(spent / br.amount * 100), 1) if br.amount > 0 else 0
        categories.append(
            {
                "id": br.id,
                "name": br.category.name,
                "amount": float(br.amount),
                "spent": float(spent),
                "percent": min(pct, 100),
            }
        )

    return {
        "totalAmount": float(total_amount),
        "totalSpent": float(total_spent),
        "categories": categories,
        "budget_type": budget_type,
        "period": period,
    }
