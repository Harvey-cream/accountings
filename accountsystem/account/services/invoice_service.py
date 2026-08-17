"""
AI 发票业务能力（抬头信息的查询与增改删）。

口径与人用 API（GetInvoiceListView / SaveInvoiceView / DeleteInvoiceView）一致：
列表按创建时间倒序；name（抬头名称）与 tax_id（税号）为必填。
「默认抬头」定义为最近创建的一条。

不处理 HTTP、鉴权、Serializer、Agent 编排。
"""

from __future__ import annotations

from decimal import Decimal

from ..models import TransactionInvoice
from .errors import ServiceError


def _to_decimal(value, field: str = "金额") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as e:
        raise ServiceError(f"{field}格式错误") from e


def _invoice_row(item: TransactionInvoice) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "tax_id": item.tax_id,
        "amount": float(item.amount),
        "address": item.address or "",
        "phone": item.phone or "",
        "bank": item.bank or "",
        "account": item.account or "",
        "remark": item.remark or "",
    }


def _base_qs(user):
    return TransactionInvoice.objects.filter(user=user).order_by("-create_time", "-id")


def list_invoices(user, *, limit: int = 20) -> list[dict]:
    """历史发票抬头列表。"""
    return [_invoice_row(i) for i in _base_qs(user)[: max(int(limit), 1)]]


def search_invoice(user, *, keyword: str | None = None, limit: int = 10) -> list[dict]:
    """按抬头名称或税号模糊搜索，供改/删前定位。"""
    qs = _base_qs(user)
    if keyword and keyword.strip():
        text = keyword.strip()
        qs = qs.filter(name__icontains=text) | qs.filter(tax_id__icontains=text)
        qs = qs.distinct()
    return [_invoice_row(i) for i in qs[: max(int(limit), 1)]]


def _get_invoice(user, invoice_id) -> TransactionInvoice:
    try:
        return TransactionInvoice.objects.get(id=invoice_id, user=user)
    except TransactionInvoice.DoesNotExist as e:
        raise ServiceError("发票信息不存在或无权操作") from e


def get_invoice_detail(user, *, invoice_id=None, name: str | None = None) -> dict:
    """按 id 或抬头名称取完整发票信息。"""
    if invoice_id is not None:
        return _invoice_row(_get_invoice(user, invoice_id))
    if name and name.strip():
        item = _base_qs(user).filter(name__icontains=name.strip()).first()
        if item is None:
            raise ServiceError("没有找到该抬头的发票信息")
        return _invoice_row(item)
    raise ServiceError("请提供发票 id 或抬头名称")


def get_invoice_header(user, *, name: str | None = None) -> dict:
    """只取报销填单最常用的抬头 + 税号。不传 name 时取默认抬头。"""
    if name and name.strip():
        detail = get_invoice_detail(user, name=name)
    else:
        detail = get_default_invoice(user)
    return {"id": detail["id"], "name": detail["name"], "tax_id": detail["tax_id"]}


def get_default_invoice(user) -> dict:
    """默认抬头：最近创建的一条。"""
    item = _base_qs(user).first()
    if item is None:
        raise ServiceError("还没有保存过发票抬头")
    return _invoice_row(item)


def create_invoice(
    user,
    *,
    name: str,
    tax_id: str,
    amount=0,
    address: str = "",
    phone: str = "",
    bank: str = "",
    account: str = "",
    remark: str = "",
) -> dict:
    """新增发票抬头。name 与 tax_id 必填（与人用 API 校验一致）。"""
    if not (name or "").strip():
        raise ServiceError("请提供发票抬头名称")
    if not (tax_id or "").strip():
        raise ServiceError("请提供税号")
    invoice = TransactionInvoice.objects.create(
        user=user,
        name=name.strip(),
        tax_id=tax_id.strip(),
        amount=_to_decimal(amount),
        address=address or "",
        phone=phone or "",
        bank=bank or "",
        account=account or "",
        remark=remark or "",
    )
    return _invoice_row(invoice)


def update_invoice(
    user,
    invoice_id,
    *,
    name: str | None = None,
    tax_id: str | None = None,
    amount=None,
    address: str | None = None,
    phone: str | None = None,
    bank: str | None = None,
    account: str | None = None,
    remark: str | None = None,
) -> dict:
    """更新发票抬头信息。"""
    invoice = _get_invoice(user, invoice_id)
    if name is not None and name.strip():
        invoice.name = name.strip()
    if tax_id is not None and tax_id.strip():
        invoice.tax_id = tax_id.strip()
    if amount is not None:
        invoice.amount = _to_decimal(amount)
    if address is not None:
        invoice.address = address
    if phone is not None:
        invoice.phone = phone
    if bank is not None:
        invoice.bank = bank
    if account is not None:
        invoice.account = account
    if remark is not None:
        invoice.remark = remark
    invoice.save()
    return _invoice_row(invoice)


def delete_invoice(user, invoice_id) -> dict:
    """删除发票抬头，返回被删记录快照。"""
    invoice = _get_invoice(user, invoice_id)
    snapshot = _invoice_row(invoice)
    invoice.delete()
    return snapshot
