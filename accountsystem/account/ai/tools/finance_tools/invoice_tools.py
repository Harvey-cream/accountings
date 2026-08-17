"""发票 Tools → invoice_service。每个 Tool 独立定义。"""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from account.services import invoice_service

from .common import run_service

# ----- list_invoices -----


class ListInvoiceInput(BaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="最多返回条数")


def list_invoices_tool(user) -> StructuredTool:
    def list_invoices(limit: int = 20) -> str:
        return run_service(
            lambda: invoice_service.list_invoices(user, limit=limit),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=list_invoices,
        name="list_invoices",
        description="列出用户保存过的发票抬头（按最近创建排序）。",
        args_schema=ListInvoiceInput,
    )


# ----- search_invoice -----


class SearchInvoiceInput(BaseModel):
    keyword: str | None = Field(default=None, description="抬头名称或税号关键词")
    limit: int = Field(default=10, ge=1, le=50, description="最多返回条数")


def search_invoice_tool(user) -> StructuredTool:
    def search_invoice(keyword: str | None = None, limit: int = 10) -> str:
        return run_service(
            lambda: invoice_service.search_invoice(user, keyword=keyword, limit=limit),
            ok_message="搜索成功",
        )

    return StructuredTool.from_function(
        func=search_invoice,
        name="search_invoice",
        description="按抬头名称或税号搜索发票信息，用于改/删前定位（用户不会说 id）。",
        args_schema=SearchInvoiceInput,
    )


# ----- get_invoice_detail -----


class GetInvoiceDetailInput(BaseModel):
    invoice_id: int | None = Field(default=None, description="发票信息 ID，可选")
    name: str | None = Field(default=None, description="抬头名称关键词，可选")


def get_invoice_detail_tool(user) -> StructuredTool:
    def get_invoice_detail(invoice_id: int | None = None, name: str | None = None) -> str:
        return run_service(
            lambda: invoice_service.get_invoice_detail(user, invoice_id=invoice_id, name=name),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=get_invoice_detail,
        name="get_invoice_detail",
        description="取某个抬头的完整开票信息（含地址、电话、开户行、账号）。",
        args_schema=GetInvoiceDetailInput,
    )


# ----- get_invoice_header -----


class GetInvoiceHeaderInput(BaseModel):
    name: str | None = Field(default=None, description="抬头名称关键词；不传则取默认抬头")


def get_invoice_header_tool(user) -> StructuredTool:
    def get_invoice_header(name: str | None = None) -> str:
        return run_service(
            lambda: invoice_service.get_invoice_header(user, name=name),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=get_invoice_header,
        name="get_invoice_header",
        description="只取报销填单要用的抬头名称与税号。用户问“抬头/税号是多少”时用。",
        args_schema=GetInvoiceHeaderInput,
    )


# ----- get_default_invoice -----


class EmptyInput(BaseModel):
    pass


def get_default_invoice_tool(user) -> StructuredTool:
    def get_default_invoice() -> str:
        return run_service(
            lambda: invoice_service.get_default_invoice(user),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=get_default_invoice,
        name="get_default_invoice",
        description="取默认发票信息（最近创建的一条）。用户没指明具体抬头时用。",
        args_schema=EmptyInput,
    )


# ----- create_invoice -----


class CreateInvoiceInput(BaseModel):
    name: str = Field(..., description="发票抬头名称（公司全称）")
    tax_id: str = Field(..., description="纳税人识别号 / 税号")
    amount: float = Field(default=0, description="开票金额，可选")
    address: str = Field(default="", description="注册地址")
    phone: str = Field(default="", description="联系电话")
    bank: str = Field(default="", description="开户银行")
    account: str = Field(default="", description="银行账号")
    remark: str = Field(default="", description="备注")


def create_invoice_tool(user) -> StructuredTool:
    def create_invoice(
        name: str,
        tax_id: str,
        amount: float = 0,
        address: str = "",
        phone: str = "",
        bank: str = "",
        account: str = "",
        remark: str = "",
    ) -> str:
        return run_service(
            lambda: invoice_service.create_invoice(
                user,
                name=name,
                tax_id=tax_id,
                amount=amount,
                address=address,
                phone=phone,
                bank=bank,
                account=account,
                remark=remark,
            ),
            ok_message="发票信息已保存",
        )

    return StructuredTool.from_function(
        func=create_invoice,
        name="create_invoice",
        description="保存一条新的发票抬头信息。抬头名称与税号必填。",
        args_schema=CreateInvoiceInput,
    )


# ----- update_invoice -----


class UpdateInvoiceInput(BaseModel):
    invoice_id: int = Field(..., description="要修改的发票信息 ID")
    name: str | None = Field(default=None, description="新抬头名称，可选")
    tax_id: str | None = Field(default=None, description="新税号，可选")
    amount: float | None = Field(default=None, description="新开票金额，可选")
    address: str | None = Field(default=None, description="新注册地址，可选")
    phone: str | None = Field(default=None, description="新联系电话，可选")
    bank: str | None = Field(default=None, description="新开户银行，可选")
    account: str | None = Field(default=None, description="新银行账号，可选")
    remark: str | None = Field(default=None, description="新备注，可选")


def update_invoice_tool(user) -> StructuredTool:
    def update_invoice(
        invoice_id: int,
        name: str | None = None,
        tax_id: str | None = None,
        amount: float | None = None,
        address: str | None = None,
        phone: str | None = None,
        bank: str | None = None,
        account: str | None = None,
        remark: str | None = None,
    ) -> str:
        return run_service(
            lambda: invoice_service.update_invoice(
                user,
                invoice_id,
                name=name,
                tax_id=tax_id,
                amount=amount,
                address=address,
                phone=phone,
                bank=bank,
                account=account,
                remark=remark,
            ),
            ok_message="发票信息已更新",
        )

    return StructuredTool.from_function(
        func=update_invoice,
        name="update_invoice",
        description="按 ID 修改已保存的发票抬头信息。",
        args_schema=UpdateInvoiceInput,
    )


# ----- delete_invoice -----


class DeleteInvoiceInput(BaseModel):
    invoice_id: int = Field(..., description="要删除的发票信息 ID（来自 search/list 结果）")


def delete_invoice_tool(user) -> StructuredTool:
    def delete_invoice(invoice_id: int) -> str:
        return run_service(
            lambda: invoice_service.delete_invoice(user, invoice_id),
            ok_message="发票信息已删除",
        )

    return StructuredTool.from_function(
        func=delete_invoice,
        name="delete_invoice",
        description="删除一条发票抬头信息。先用 search_invoice 定位，再传入结果中的 id。",
        args_schema=DeleteInvoiceInput,
    )


def build_invoice_tools(user) -> list[StructuredTool]:
    return [
        list_invoices_tool(user),
        search_invoice_tool(user),
        get_invoice_detail_tool(user),
        get_invoice_header_tool(user),
        get_default_invoice_tool(user),
        create_invoice_tool(user),
        update_invoice_tool(user),
        delete_invoice_tool(user),
    ]
