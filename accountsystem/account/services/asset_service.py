"""
AI 资产业务能力（账户查询 / 汇总 / 结构 / 增改删）。

口径与人用 API（GetAssetListView / SaveAssetAccountView）保持一致：
- 资产、负债均按绝对值累计，净资产 = 总资产 - 总负债；
- 分组名取资产图标名称，debt 类型统一并入「负债」组；
- 信用卡(3) / 负债(6) 两类图标默认按负债处理（与前端 asset_edit 的判定一致）。

不处理 HTTP、鉴权、Serializer、Agent 编排。
"""

from __future__ import annotations

from decimal import Decimal

from ..models import AssetAccount, AssetIcon
from .errors import ServiceError

# 与前端 asset_edit.vue 一致：这两类图标默认记为负债
_DEBT_ICON_IDS = {3, 6}
_DEBT_GROUP = "负债"


def _to_decimal(value, field: str = "金额") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as e:
        raise ServiceError(f"{field}格式错误") from e


def _resolve_asset_icon(asset_type) -> AssetIcon:
    """按 id 或名称解析资产类型图标。"""
    if asset_type is None or str(asset_type).strip() == "":
        raise ServiceError("请提供资产类型，如 现金 / 储蓄卡 / 信用卡")
    text = str(asset_type).strip()
    icon = None
    if text.isdigit():
        icon = AssetIcon.objects.filter(id=int(text)).first()
    if icon is None:
        icon = AssetIcon.objects.filter(name=text).first()
    if icon is None:
        options = "、".join(AssetIcon.objects.values_list("name", flat=True))
        raise ServiceError(f"资产类型不存在：{text}。可选：{options}")
    return icon


def _norm_account_type(account_type: str | None, icon: AssetIcon) -> str:
    if account_type in ("asset", "资产"):
        return "asset"
    if account_type in ("debt", "负债"):
        return "debt"
    return "debt" if icon.id in _DEBT_ICON_IDS else "asset"


def _group_name(acc: AssetAccount) -> str:
    name = acc.asset_type.name
    if acc.type == "debt" and name != _DEBT_GROUP:
        return _DEBT_GROUP
    return name


def _account_row(acc: AssetAccount) -> dict:
    amount = abs(acc.balance)
    return {
        "id": acc.id,
        "name": acc.name,
        "asset_type": acc.asset_type.name,
        "type": acc.type,
        "balance": float(-amount if acc.type == "debt" else amount),
        "is_included_in_total": acc.is_included_in_total,
        "remark": acc.remark or "",
    }


def _all_accounts(user):
    return (
        AssetAccount.objects.filter(user=user)
        .select_related("asset_type")
        .order_by("type", "create_time")
    )


def _totals(accounts) -> tuple[Decimal, Decimal]:
    total_asset = Decimal("0")
    total_debt = Decimal("0")
    for acc in accounts:
        if acc.type == "debt":
            total_debt += abs(acc.balance)
        else:
            total_asset += abs(acc.balance)
    return total_asset, total_debt


def list_asset_types() -> list[dict]:
    """可选的资产类型（记账户时供用户挑选）。"""
    return [
        {"id": i.id, "name": i.name, "default_type": "debt" if i.id in _DEBT_ICON_IDS else "asset"}
        for i in AssetIcon.objects.all().order_by("id")
    ]


def query_asset_summary(user) -> dict:
    """总资产 / 总负债 / 净资产。"""
    accounts = list(_all_accounts(user))
    total_asset, total_debt = _totals(accounts)
    return {
        "total_asset": float(total_asset),
        "total_debt": float(total_debt),
        "net_asset": float(total_asset - total_debt),
        "account_count": len(accounts),
    }


def query_asset_accounts(user, *, account_type: str | None = None) -> dict:
    """按大类分组的账户明细 + 汇总。account_type 可选 asset / debt。"""
    accounts = list(_all_accounts(user))
    total_asset, total_debt = _totals(accounts)

    if account_type in ("asset", "资产"):
        accounts = [a for a in accounts if a.type == "asset"]
    elif account_type in ("debt", "负债"):
        accounts = [a for a in accounts if a.type == "debt"]

    grouped: dict[str, dict] = {}
    for acc in accounts:
        name = _group_name(acc)
        group = grouped.setdefault(name, {"name": name, "total": 0.0, "items": []})
        row = _account_row(acc)
        group["items"].append(row)
        group["total"] = round(group["total"] + row["balance"], 2)

    return {
        "groups": list(grouped.values()),
        "summary": {
            "total_asset": float(total_asset),
            "total_debt": float(total_debt),
            "net_asset": float(total_asset - total_debt),
        },
    }


def query_asset_account(user, *, account_id=None, name: str | None = None) -> dict:
    """按 id 或名称查单个账户。名称多个命中时返回第一个。"""
    qs = _all_accounts(user)
    if account_id is not None:
        acc = qs.filter(id=account_id).first()
    elif name:
        acc = qs.filter(name__icontains=name.strip()).first()
    else:
        raise ServiceError("请提供账户 id 或名称")
    if acc is None:
        raise ServiceError("账户不存在或无权查看")
    return _account_row(acc)


def search_asset_accounts(user, *, name: str | None = None, limit: int = 5) -> list[dict]:
    """按名称模糊搜账户，供改/删前定位。"""
    qs = _all_accounts(user)
    if name:
        qs = qs.filter(name__icontains=name.strip())
    return [_account_row(a) for a in qs[: max(int(limit), 1)]]


def query_asset_structure(user) -> dict:
    """资产结构：资产/负债占比与各大类占比。"""
    accounts = list(_all_accounts(user))
    total_asset, total_debt = _totals(accounts)
    base = total_asset + total_debt

    groups: dict[str, Decimal] = {}
    for acc in accounts:
        groups[_group_name(acc)] = groups.get(_group_name(acc), Decimal("0")) + abs(acc.balance)

    def _pct(v: Decimal) -> float:
        return round(float(v) / float(base) * 100, 1) if base else 0.0

    return {
        "total_asset": float(total_asset),
        "total_debt": float(total_debt),
        "net_asset": float(total_asset - total_debt),
        "asset_percent": _pct(total_asset),
        "debt_percent": _pct(total_debt),
        "groups": [
            {"name": k, "amount": float(v), "percent": _pct(v)}
            for k, v in sorted(groups.items(), key=lambda kv: kv[1], reverse=True)
        ],
    }


def create_asset_account(
    user,
    *,
    name: str,
    asset_type,
    balance=0,
    account_type: str | None = None,
    is_included_in_total: bool = True,
    remark: str = "",
) -> dict:
    """新增资产/负债账户。"""
    if not (name or "").strip():
        raise ServiceError("请提供账户名称")
    icon = _resolve_asset_icon(asset_type)
    account = AssetAccount.objects.create(
        user=user,
        name=name.strip(),
        asset_type=icon,
        balance=_to_decimal(balance, "余额"),
        type=_norm_account_type(account_type, icon),
        is_included_in_total=bool(is_included_in_total),
        remark=remark or "",
    )
    return _account_row(account)


def _get_account(user, account_id) -> AssetAccount:
    try:
        return AssetAccount.objects.select_related("asset_type").get(id=account_id, user=user)
    except AssetAccount.DoesNotExist as e:
        raise ServiceError("账户不存在或无权操作") from e


def update_asset_account(
    user,
    account_id,
    *,
    name: str | None = None,
    asset_type=None,
    balance=None,
    account_type: str | None = None,
    is_included_in_total: bool | None = None,
    remark: str | None = None,
) -> dict:
    """更新账户信息（balance 为覆盖式设置）。"""
    account = _get_account(user, account_id)
    if name is not None and name.strip():
        account.name = name.strip()
    if asset_type is not None:
        icon = _resolve_asset_icon(asset_type)
        account.asset_type = icon
        if account_type is None:
            account.type = _norm_account_type(None, icon)
    if account_type is not None:
        account.type = _norm_account_type(account_type, account.asset_type)
    if balance is not None:
        account.balance = _to_decimal(balance, "余额")
    if is_included_in_total is not None:
        account.is_included_in_total = bool(is_included_in_total)
    if remark is not None:
        account.remark = remark
    account.save()
    return _account_row(account)


def adjust_asset_balance(user, account_id, *, delta) -> dict:
    """按增量调整余额（收入到账/支出扣减）。delta 可为负。"""
    account = _get_account(user, account_id)
    before = account.balance
    account.balance = before + _to_decimal(delta, "调整金额")
    account.save(update_fields=["balance", "update_time"])
    row = _account_row(account)
    row["balance_before"] = float(before)
    row["delta"] = float(_to_decimal(delta, "调整金额"))
    return row


def delete_asset_account(user, account_id) -> dict:
    """删除账户，返回被删账户快照。"""
    account = _get_account(user, account_id)
    snapshot = _account_row(account)
    account.delete()
    return snapshot
