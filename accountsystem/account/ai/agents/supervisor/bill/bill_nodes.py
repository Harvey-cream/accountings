"""Bill Workflow 节点实现。节点只调 Tool，不碰 ORM。"""

from __future__ import annotations

import json
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content, log_agent_exc

from .bill_prompt import (
    ACTION_LABEL,
    BILL_INTENT_SYSTEM,
    BILL_LOCATOR_SYSTEM,
    BILL_SYSTEM,
    BILL_TARGET_HINT,
    CONFIRM_MANY,
    CONFIRM_ONE,
    CONFIRM_OPTION,
    INTENT_GUIDE,
    NOT_FOUND,
)
from .bill_schemas import BillIntent, BillLocator
from .bill_state import BillAgentState

_ID_RE = re.compile(r"#\s*(\d+)")
_AFFIRM = ("确认", "确定", "是的", "对的", "没错", "可以", "好的", "删吧", "改吧", "就它", "yes", "ok")
_MAX_CANDIDATES = 5


# ----- 1. context_prepare -----


def context_prepare_node(state: BillAgentState) -> dict:
    """合并历史与本轮输入；若上一轮是确认问句且用户应答肯定，则续跑原操作。"""
    text = (state.get("input") or "").strip()
    update: dict = {"messages": [HumanMessage(content=text)], "loops": 0}

    pending = _pending_confirm(state.get("messages") or [], text)
    if pending:
        update["intent"] = pending["intent"]
        update["target_bill"] = {"id": pending["bill_id"]}
        update["confirmed"] = True
    return update


def _pending_confirm(history: list, text: str) -> dict | None:
    """从上一条助手确认问句里回收账单编号与动作，等价于一次 resume。"""
    if not any(word in text for word in _AFFIRM):
        return None

    asked = ""
    for msg in reversed(history):
        if isinstance(msg, AIMessage):
            asked = extract_content(msg)
            break
    if not asked:
        return None

    # 多选场景下用户会自己带编号，优先取用户这句里的
    match = _ID_RE.search(text) or _ID_RE.search(asked)
    if not match:
        return None

    intent = "delete" if "删除" in asked else "update" if "修改" in asked else ""
    if not intent:
        return None
    return {"bill_id": int(match.group(1)), "intent": intent}


# ----- 2. intent_router -----


def make_intent_router_node(model=llm):
    """账单任务分类，只看文本，不访问数据库。"""
    router = model.with_structured_output(BillIntent)

    def intent_router_node(state: BillAgentState) -> dict:
        if state.get("intent"):
            return {}
        text = state.get("input") or ""
        try:
            decision = router.invoke(
                [SystemMessage(content=BILL_INTENT_SYSTEM), HumanMessage(content=text)]
            )
            return {"intent": decision.intent}
        except Exception as e:
            log_agent_exc("BILL_INTENT", e, input=text[:60])
            return {"intent": "query"}

    return intent_router_node


# ----- 3. bill_agent -----


def make_bill_agent_node(tools: list, model=llm):
    """按 intent 决定本轮该用哪些工具，由 LLM 发起 tool_calls。"""
    agent_llm = model.bind_tools(tools)

    def bill_agent_node(state: BillAgentState) -> dict:
        guide = INTENT_GUIDE.get(state.get("intent") or "", "")
        system = SystemMessage(content=f"{BILL_SYSTEM}\n\n{guide}".strip())
        reply = agent_llm.invoke([system, *(state.get("messages") or [])])
        return {"messages": [reply], "loops": int(state.get("loops") or 0) + 1}

    return bill_agent_node


# ----- 5. mutation_check -----


def make_mutation_check_node(tools_by_name: dict, model=llm):
    """改单/删单前先定位目标，避免误改误删。"""
    locator = model.with_structured_output(BillLocator)
    search_tool = tools_by_name["search_bills"]

    def mutation_check_node(state: BillAgentState) -> dict:
        target = state.get("target_bill") or {}
        if target.get("id"):
            return _located(state, target)

        text = state.get("input") or ""
        try:
            hint = locator.invoke(
                [SystemMessage(content=BILL_LOCATOR_SYSTEM), HumanMessage(content=text)]
            )
        except Exception as e:
            log_agent_exc("BILL_LOCATOR", e, input=text[:60])
            hint = BillLocator()

        if hint.bill_id:
            return _located(state, {"id": hint.bill_id})

        rows = _tool_rows(
            search_tool.invoke(
                {
                    "keyword": hint.keyword,
                    "category": hint.category,
                    "days": hint.days,
                    "bill_type": hint.bill_type,
                    "limit": _MAX_CANDIDATES,
                }
            )
        )
        if not rows:
            return {"result": {"success": False, "message": NOT_FOUND, "data": {}}}
        if len(rows) == 1:
            return _located(state, rows[0], candidates=rows)
        return {"candidates": rows[:_MAX_CANDIDATES], "need_confirm": True}

    return mutation_check_node


def _located(state: BillAgentState, target: dict, candidates: list | None = None) -> dict:
    """唯一命中：已确认就带着 id 去执行，未确认就先问一句。"""
    update: dict = {"target_bill": target, "need_confirm": not state.get("confirmed")}
    if candidates:
        update["candidates"] = candidates
    if state.get("confirmed"):
        update["messages"] = [
            SystemMessage(
                content=BILL_TARGET_HINT.format(bill=json.dumps(target, ensure_ascii=False))
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


# ----- 6. human_confirm -----


def human_confirm_node(state: BillAgentState) -> dict:
    """高危操作前的口头确认。

    接口层没有 resume 端点，确认问句作为本轮回复返回；用户下一轮应答“确认”时，
    context_prepare 从问句里回收 #id 续跑，效果等同 interrupt/resume。
    """
    action = ACTION_LABEL.get(state.get("intent") or "", "操作")
    candidates = state.get("candidates") or []
    target = state.get("target_bill") or {}

    if len(candidates) > 1:
        options = "；".join(_option_text(row) for row in candidates)
        question = CONFIRM_MANY.format(count=len(candidates), action=action, options=options)
    else:
        row = candidates[0] if candidates else target
        question = CONFIRM_ONE.format(
            action=action,
            date=row.get("date") or "",
            remark=row.get("remark") or row.get("category") or "这笔",
            amount=_money(row.get("amount")),
            bill_id=row.get("id") or target.get("id") or "",
        )

    return {
        "messages": [AIMessage(content=question)],
        "result": {
            "success": True,
            "message": question,
            "data": {"need_confirm": True, "candidates": candidates or [target]},
        },
    }


def _option_text(row: dict) -> str:
    return CONFIRM_OPTION.format(
        date=row.get("date") or "",
        remark=row.get("remark") or row.get("category") or "",
        amount=_money(row.get("amount")),
        bill_id=row.get("id") or "",
    )


def _money(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value or "")
    return str(int(number)) if number.is_integer() else f"{number:g}"


# ----- 7. result_formatter -----


def result_formatter_node(state: BillAgentState) -> dict:
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
                "target_bill": state.get("target_bill"),
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
