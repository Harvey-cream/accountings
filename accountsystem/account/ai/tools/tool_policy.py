"""各域工具授权策略：按 action + 确认态裁剪本轮可绑定的工具。

原则（D2 安全收口）：
  1. 默认只读。只有 intent 是写操作、且本轮已确认时，才额外放行该动作的写工具。
  2. 只放行"意图明确的那一个"写工具。确认后的 update 拿不到 delete，避免扩大授权面。
  3. 未确认的写意图只读绑定——LLM 即使想写，手上也没有可调用的写工具。

纯函数、无状态、只依赖工具名常量，供各域 agent 节点按需调用。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# 各域只读工具（查询 / 目标定位阶段允许的全部工具）
READ_TOOLS: dict[str, tuple[str, ...]] = {
    "bill": ("query_bills", "search_bills"),
    "budget": ("query_budget", "budget_advice"),
    "asset": (
        "query_asset_summary",
        "query_asset_accounts",
        "query_asset_account",
        "search_asset_accounts",
        "query_asset_structure",
        "list_asset_types",
    ),
    "invoice": (
        "list_invoices",
        "search_invoice",
        "get_invoice_detail",
        "get_invoice_header",
        "get_default_invoice",
    ),
}

# 各域 action → 该动作允许的写工具（budget 的 set_budget 内部再分新建/更新）
WRITE_TOOLS: dict[str, dict[str, tuple[str, ...]]] = {
    "bill": {
        "create": ("create_bill",),
        "batch_create": ("batch_create_bills",),
        "update": ("update_bill",),
        "delete": ("delete_bill",),
    },
    "budget": {
        "set_budget": ("create_budget", "update_budget"),
    },
    "asset": {
        "create": ("create_asset_account",),
        "update": ("update_asset_account",),
        "delete": ("delete_asset_account",),
        "adjust_balance": ("adjust_asset_balance",),
    },
    "invoice": {
        "create": ("create_invoice",),
        "update": ("update_invoice",),
        "delete": ("delete_invoice",),
    },
}

# 命中越权工具时的统一回复：不改数据，退回询问。
BLOCKED_MESSAGE = "这次我不会直接改动你的数据。请先确认要操作的是哪一条～"


def allowed_tool_names(
    domain: str,
    intent: str,
    confirmed: bool,
    *,
    always: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """本轮该绑给 LLM 的工具名（有序、去重）。

    always：与读写无关的常驻工具（如预算域的知识库检索）。
    """
    names = [*READ_TOOLS.get(domain, ()), *always]
    if confirmed:
        names.extend(WRITE_TOOLS.get(domain, {}).get(intent or "", ()))
    return tuple(dict.fromkeys(names))


def select_tools(tools_by_name: dict, names: tuple[str, ...]) -> list:
    """按名字取回工具对象（保持 names 顺序）；名字缺失直接跳过。"""
    return [tools_by_name[n] for n in names if n in tools_by_name]


def blocked_write_calls(reply, allowed_names: tuple[str, ...]) -> list[str]:
    """第二道闸：LLM 实际发出的 tool_calls 里越过白名单的工具名（通常为空）。"""
    allowed = set(allowed_names)
    blocked: list[str] = []
    for call in getattr(reply, "tool_calls", None) or ():
        name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
        if name and name not in allowed:
            blocked.append(str(name))
    if blocked:
        logger.warning(
            "[TOOL-GRANT] blocked unauthorized tool call(s): %s allowed=%s",
            blocked,
            sorted(allowed),
        )
    return blocked
