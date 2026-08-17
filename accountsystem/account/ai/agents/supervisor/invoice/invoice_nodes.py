"""Invoice Workflow 节点实现。节点只调 Tool，不碰 ORM。"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content, log_agent_exc

from .invoice_prompt import (
    ACTION_LABEL,
    INTENT_GUIDE,
    INVOICE_INTENT_SYSTEM,
    INVOICE_LOCATOR_SYSTEM,
    INVOICE_SYSTEM,
    INVOICE_TARGET_HINT,
    NOT_FOUND,
)
from .invoice_schemas import InvoiceIntent, InvoiceLocator
from .invoice_state import InvoiceAgentState

_MAX_CANDIDATES = 5


def _origin_text(state: InvoiceAgentState) -> str:
    """本轮真正要处理的用户诉求。确认回合回历史里取用户原话。

    是否确认只看 state.confirmed（前端布尔回传），不解析文案。
    """
    text = (state.get("input") or "").strip()
    if not state.get("confirmed"):
        return text
    for msg in reversed(state.get("messages") or []):
        if not isinstance(msg, HumanMessage):
            continue
        content = extract_content(msg).strip()
        if content and content != text:
            return content
    return text


# ----- 1. context_prepare -----


def context_prepare_node(state: InvoiceAgentState) -> dict:
    """合并历史与本轮输入。结构化确认已由外壳写入 intent/target_invoice/confirmed。"""
    text = (state.get("input") or "").strip()
    return {"messages": [HumanMessage(content=text)], "loops": 0}


# ----- 2. intent_router -----


def make_intent_router_node(model=llm):
    """发票任务分类，只看文本，不访问数据库。"""
    router = model.with_structured_output(InvoiceIntent)

    def intent_router_node(state: InvoiceAgentState) -> dict:
        if state.get("intent"):
            return {}
        text = state.get("input") or ""
        try:
            decision = router.invoke(
                [SystemMessage(content=INVOICE_INTENT_SYSTEM), HumanMessage(content=text)]
            )
            return {"intent": decision.intent}
        except Exception as e:
            log_agent_exc("INVOICE_INTENT", e, input=text[:60])
            return {"intent": "query"}

    return intent_router_node


# ----- 3. invoice_agent -----


def make_invoice_agent_node(tools: list, model=llm):
    """按 intent 决定本轮该用哪些工具，由 LLM 发起 tool_calls。"""
    agent_llm = model.bind_tools(tools)

    def invoice_agent_node(state: InvoiceAgentState) -> dict:
        guide = INTENT_GUIDE.get(state.get("intent") or "", "")
        system = SystemMessage(content=f"{INVOICE_SYSTEM}\n\n{guide}".strip())
        reply = agent_llm.invoke([system, *(state.get("messages") or [])])
        return {"messages": [reply], "loops": int(state.get("loops") or 0) + 1}

    return invoice_agent_node


# ----- 4. mutation_check -----


def make_mutation_check_node(tools_by_name: dict, model=llm):
    """改/删前先定位目标抬头，避免误改误删。"""
    locator = model.with_structured_output(InvoiceLocator)
    search_tool = tools_by_name["search_invoice"]

    def mutation_check_node(state: InvoiceAgentState) -> dict:
        target = state.get("target_invoice") or {}
        if target.get("id"):
            return _located(state, target)

        text = _origin_text(state)
        try:
            hint = locator.invoke(
                [SystemMessage(content=INVOICE_LOCATOR_SYSTEM), HumanMessage(content=text)]
            )
        except Exception as e:
            log_agent_exc("INVOICE_LOCATOR", e, input=text[:60])
            hint = InvoiceLocator()

        if hint.invoice_id:
            return _located(state, {"id": hint.invoice_id})

        rows = _tool_rows(
            search_tool.invoke({"keyword": hint.keyword, "limit": _MAX_CANDIDATES})
        )
        if not rows:
            return {"result": {"success": False, "message": NOT_FOUND, "data": {}}}
        if len(rows) == 1:
            return _located(state, rows[0], candidates=rows)
        return {"candidates": rows[:_MAX_CANDIDATES], "need_confirm": True}

    return mutation_check_node


def _located(state: InvoiceAgentState, target: dict, candidates: list | None = None) -> dict:
    """唯一命中：已确认就带着 id 去执行，未确认就先问一句。"""
    update: dict = {"target_invoice": target, "need_confirm": not state.get("confirmed")}
    if candidates:
        update["candidates"] = candidates
    if state.get("confirmed"):
        update["messages"] = [
            SystemMessage(
                content=INVOICE_TARGET_HINT.format(invoice=json.dumps(target, ensure_ascii=False))
            )
        ]
    return update


def _tool_rows(raw) -> list[dict]:
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return []
    if not isinstance(payload, dict) or not payload.get("success"):
        return []
    data = payload.get("data")
    return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []


# ----- 5. human_confirm -----


def human_confirm_node(state: InvoiceAgentState) -> dict:
    """高危操作前输出确认卡片数据，等前端点确认/取消后续跑。"""
    intent = state.get("intent") or ""
    action = ACTION_LABEL.get(intent, "操作")
    candidates = state.get("candidates") or []
    target = state.get("target_invoice") or {}
    rows = candidates or ([target] if target else [])

    if len(rows) > 1:
        question = f"找到 {len(rows)} 条相近的发票信息，请点选要{action}的那一条～"
    else:
        question = f"确认{action}这条发票信息吗？"

    return {
        "messages": [AIMessage(content=question)],
        "result": {
            "success": True,
            "message": question,
            "data": {
                "need_confirm": True,
                "entity": "invoice",
                "action": intent,
                "candidates": rows,
            },
        },
    }


# ----- 6. result_formatter -----


def result_formatter_node(state: InvoiceAgentState) -> dict:
    """统一出参 {success, message, data}，messages 保留给 _graph_to_result 抽取工具步骤。"""
    if state.get("result"):
        return {}

    messages = state.get("messages") or []
    text = extract_content(messages[-1]).strip() if messages else ""
    success = True
    for msg in messages:
        if isinstance(msg, ToolMessage):
            payload = _tool_payload(msg.content)
            if payload is not None:
                success = bool(payload.get("success"))
    return {
        "result": {
            "success": success,
            "message": text,
            "data": {
                "intent": state.get("intent") or "",
                "target_invoice": state.get("target_invoice"),
            },
        }
    }


def _tool_payload(raw) -> dict | None:
    if not isinstance(raw, str):
        return None
    try:
        payload = json.loads(raw)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None
