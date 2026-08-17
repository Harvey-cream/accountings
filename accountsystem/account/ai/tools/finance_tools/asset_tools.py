"""资产 Tools → asset_service。每个 Tool 独立定义，只读与写操作分开组装。"""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from account.services import asset_service

from .common import run_service

# ----- query_asset_summary -----


class EmptyInput(BaseModel):
    pass


def query_asset_summary_tool(user) -> StructuredTool:
    def query_asset_summary() -> str:
        return run_service(
            lambda: asset_service.query_asset_summary(user),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=query_asset_summary,
        name="query_asset_summary",
        description="查询总资产、总负债、净资产与账户数量。回答“我有多少钱/净资产多少”时用。",
        args_schema=EmptyInput,
    )


# ----- query_asset_accounts -----


class QueryAssetAccountsInput(BaseModel):
    account_type: str | None = Field(
        default=None, description="可选过滤：asset(资产)/debt(负债)；不传则全部"
    )


def query_asset_accounts_tool(user) -> StructuredTool:
    def query_asset_accounts(account_type: str | None = None) -> str:
        return run_service(
            lambda: asset_service.query_asset_accounts(user, account_type=account_type),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=query_asset_accounts,
        name="query_asset_accounts",
        description="按大类分组列出全部资产/负债账户及余额。回答“有哪些账户/各账户多少钱”时用。",
        args_schema=QueryAssetAccountsInput,
    )


# ----- query_asset_account -----


class QueryAssetAccountInput(BaseModel):
    account_id: int | None = Field(default=None, description="账户 ID，可选")
    name: str | None = Field(default=None, description="账户名称关键词，如招行、支付宝")


def query_asset_account_tool(user) -> StructuredTool:
    def query_asset_account(account_id: int | None = None, name: str | None = None) -> str:
        return run_service(
            lambda: asset_service.query_asset_account(user, account_id=account_id, name=name),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=query_asset_account,
        name="query_asset_account",
        description="按 ID 或名称查询单个账户的余额与详情。",
        args_schema=QueryAssetAccountInput,
    )


# ----- search_asset_accounts -----


class SearchAssetAccountsInput(BaseModel):
    name: str | None = Field(default=None, description="账户名称关键词，不传则返回全部")
    limit: int = Field(default=5, ge=1, le=50, description="最多返回条数")


def search_asset_accounts_tool(user) -> StructuredTool:
    def search_asset_accounts(name: str | None = None, limit: int = 5) -> str:
        return run_service(
            lambda: asset_service.search_asset_accounts(user, name=name, limit=limit),
            ok_message="搜索成功",
        )

    return StructuredTool.from_function(
        func=search_asset_accounts,
        name="search_asset_accounts",
        description="按名称模糊搜索账户，用于改/删/调整余额前定位（用户不会说账户 id）。",
        args_schema=SearchAssetAccountsInput,
    )


# ----- query_asset_structure -----


def query_asset_structure_tool(user) -> StructuredTool:
    def query_asset_structure() -> str:
        return run_service(
            lambda: asset_service.query_asset_structure(user),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=query_asset_structure,
        name="query_asset_structure",
        description="查询资产结构：资产/负债占比与各大类金额占比。回答“资产配置合不合理”时用。",
        args_schema=EmptyInput,
    )


# ----- list_asset_types -----


def list_asset_types_tool(user) -> StructuredTool:
    def list_asset_types() -> str:
        return run_service(asset_service.list_asset_types, ok_message="查询成功")

    return StructuredTool.from_function(
        func=list_asset_types,
        name="list_asset_types",
        description="列出可选的资产类型（现金、储蓄卡、信用卡等）。新建账户前不确定类型时用。",
        args_schema=EmptyInput,
    )


# ----- create_asset_account -----


class CreateAssetAccountInput(BaseModel):
    name: str = Field(..., description="账户名称，如 招商银行、支付宝")
    asset_type: str = Field(..., description="资产类型名称，如 现金/储蓄卡/信用卡/投资账户")
    balance: float = Field(default=0, description="初始余额；负债账户填欠款金额（正数）")
    account_type: str | None = Field(
        default=None, description="可选 asset/debt；不传则按资产类型自动判定"
    )
    is_included_in_total: bool = Field(default=True, description="是否计入资产总额")
    remark: str = Field(default="", description="备注")


def create_asset_account_tool(user) -> StructuredTool:
    def create_asset_account(
        name: str,
        asset_type: str,
        balance: float = 0,
        account_type: str | None = None,
        is_included_in_total: bool = True,
        remark: str = "",
    ) -> str:
        return run_service(
            lambda: asset_service.create_asset_account(
                user,
                name=name,
                asset_type=asset_type,
                balance=balance,
                account_type=account_type,
                is_included_in_total=is_included_in_total,
                remark=remark,
            ),
            ok_message="账户已创建",
        )

    return StructuredTool.from_function(
        func=create_asset_account,
        name="create_asset_account",
        description="新建一个资产或负债账户。",
        args_schema=CreateAssetAccountInput,
    )


# ----- update_asset_account -----


class UpdateAssetAccountInput(BaseModel):
    account_id: int = Field(..., description="要修改的账户 ID")
    name: str | None = Field(default=None, description="新账户名称，可选")
    asset_type: str | None = Field(default=None, description="新资产类型名称，可选")
    balance: float | None = Field(default=None, description="新余额（覆盖式设置），可选")
    account_type: str | None = Field(default=None, description="asset/debt，可选")
    is_included_in_total: bool | None = Field(default=None, description="是否计入总额，可选")
    remark: str | None = Field(default=None, description="新备注，可选")


def update_asset_account_tool(user) -> StructuredTool:
    def update_asset_account(
        account_id: int,
        name: str | None = None,
        asset_type: str | None = None,
        balance: float | None = None,
        account_type: str | None = None,
        is_included_in_total: bool | None = None,
        remark: str | None = None,
    ) -> str:
        return run_service(
            lambda: asset_service.update_asset_account(
                user,
                account_id,
                name=name,
                asset_type=asset_type,
                balance=balance,
                account_type=account_type,
                is_included_in_total=is_included_in_total,
                remark=remark,
            ),
            ok_message="账户已更新",
        )

    return StructuredTool.from_function(
        func=update_asset_account,
        name="update_asset_account",
        description="按账户 ID 修改账户名称、类型、余额或备注。余额为覆盖式设置。",
        args_schema=UpdateAssetAccountInput,
    )


# ----- adjust_asset_balance -----


class AdjustAssetBalanceInput(BaseModel):
    account_id: int = Field(..., description="要调整的账户 ID")
    delta: float = Field(..., description="余额增量，正数为增加，负数为减少")


def adjust_asset_balance_tool(user) -> StructuredTool:
    def adjust_asset_balance(account_id: int, delta: float) -> str:
        return run_service(
            lambda: asset_service.adjust_asset_balance(user, account_id, delta=delta),
            ok_message="余额已调整",
        )

    return StructuredTool.from_function(
        func=adjust_asset_balance,
        name="adjust_asset_balance",
        description="按增量调整账户余额（如“工资卡进账 8000”“信用卡还款 2000”）。与覆盖式的 update_asset_account 区分。",
        args_schema=AdjustAssetBalanceInput,
    )


# ----- delete_asset_account -----


class DeleteAssetAccountInput(BaseModel):
    account_id: int = Field(..., description="要删除的账户 ID（来自 search/query 结果）")


def delete_asset_account_tool(user) -> StructuredTool:
    def delete_asset_account(account_id: int) -> str:
        return run_service(
            lambda: asset_service.delete_asset_account(user, account_id),
            ok_message="账户已删除",
        )

    return StructuredTool.from_function(
        func=delete_asset_account,
        name="delete_asset_account",
        description="删除当前用户的一个资产账户。先用 search_asset_accounts 定位，再传入结果中的 id。",
        args_schema=DeleteAssetAccountInput,
    )


def build_asset_query_tools(user) -> list[StructuredTool]:
    """只读资产能力。供 Asset Workflow 与 CrewAI（只读）共用。"""
    return [
        query_asset_summary_tool(user),
        query_asset_accounts_tool(user),
        query_asset_account_tool(user),
        query_asset_structure_tool(user),
        search_asset_accounts_tool(user),
        list_asset_types_tool(user),
    ]


def build_asset_tools(user) -> list[StructuredTool]:
    return [
        *build_asset_query_tools(user),
        create_asset_account_tool(user),
        update_asset_account_tool(user),
        adjust_asset_balance_tool(user),
        delete_asset_account_tool(user),
    ]
