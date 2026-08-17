"""财务类 AI Tools：账单 / 预算 / 资产 / 发票 / 分析。统一经 Service 访问数据库。"""

from .analysis_tools import (
    analyze_expense_tool,
    build_analysis_tools,
    compare_periods_tool,
)
from .asset_tools import (
    adjust_asset_balance_tool,
    build_asset_query_tools,
    build_asset_tools,
    create_asset_account_tool,
    delete_asset_account_tool,
    list_asset_types_tool,
    query_asset_account_tool,
    query_asset_accounts_tool,
    query_asset_structure_tool,
    query_asset_summary_tool,
    search_asset_accounts_tool,
    update_asset_account_tool,
)
from .bill_tools import (
    batch_create_bills_tool,
    build_bill_tools,
    create_bill_tool,
    delete_bill_tool,
    query_bills_tool,
    search_bills_tool,
    update_bill_tool,
)
from .budget_tools import (
    budget_advice_tool,
    build_budget_tools,
    create_budget_tool,
    query_budget_tool,
    update_budget_tool,
)
from .invoice_tools import (
    build_invoice_tools,
    create_invoice_tool,
    delete_invoice_tool,
    get_default_invoice_tool,
    get_invoice_detail_tool,
    get_invoice_header_tool,
    list_invoices_tool,
    search_invoice_tool,
    update_invoice_tool,
)


def build_finance_tools(user) -> list:
    """组装全部财务 Tools，user 由调用方注入（鉴权后的 Django User）。"""
    return [
        *build_bill_tools(user),
        *build_budget_tools(user),
        *build_asset_tools(user),
        *build_invoice_tools(user),
        *build_analysis_tools(user),
    ]


__all__ = [
    "build_finance_tools",
    "build_bill_tools",
    "build_budget_tools",
    "build_asset_tools",
    "build_asset_query_tools",
    "build_invoice_tools",
    "build_analysis_tools",
    "create_bill_tool",
    "batch_create_bills_tool",
    "update_bill_tool",
    "query_bills_tool",
    "search_bills_tool",
    "delete_bill_tool",
    "create_budget_tool",
    "update_budget_tool",
    "query_budget_tool",
    "budget_advice_tool",
    "query_asset_summary_tool",
    "query_asset_accounts_tool",
    "query_asset_account_tool",
    "query_asset_structure_tool",
    "search_asset_accounts_tool",
    "list_asset_types_tool",
    "create_asset_account_tool",
    "update_asset_account_tool",
    "adjust_asset_balance_tool",
    "delete_asset_account_tool",
    "list_invoices_tool",
    "search_invoice_tool",
    "get_invoice_detail_tool",
    "get_invoice_header_tool",
    "get_default_invoice_tool",
    "create_invoice_tool",
    "update_invoice_tool",
    "delete_invoice_tool",
    "analyze_expense_tool",
    "compare_periods_tool",
]
