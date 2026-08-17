"""Bill Workflow 节点实现。节点只调 Tool，不碰 ORM。"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import ValidationError

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import (
    extract_content,
    log_agent_exc,
    nested_structured_output,
)

from .bill_prompt import (
    ACTION_LABEL,
    BATCH_EMPTY,
    BILL_BATCH_HINT,
    BILL_BATCH_RETRY_HINT,
    BILL_BATCH_SYSTEM,
    BILL_INTENT_SYSTEM,
    BILL_LOCATOR_SYSTEM,
    BILL_SYSTEM,
    BILL_TARGET_HINT,
    INTENT_GUIDE,
    NOT_FOUND,
)
from .bill_schemas import BillBatch, BillIntent, BillLocator
from .bill_state import BillAgentState

_MAX_CANDIDATES = 5
_MAX_DRAFTS = 20
_BATCH_MAX_RETRIES = 1


def _origin_text(state: BillAgentState) -> str:
    """本轮真正要处理的用户诉求。确认回合回历史里取用户原话。

    是否确认只看 state.confirmed（前端布尔回传），不解析文案。
    确认回合的 input 是前端占位句，messages 里刚追加的那条就是它，跳过即可。
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


def context_prepare_node(state: BillAgentState) -> dict:
    """合并历史与本轮输入。

    结构化确认（前端卡片点确认）已由外壳写入 intent/target_bill/confirmed，这里只追加消息。
    """
    text = (state.get("input") or "").strip()
    return {"messages": [HumanMessage(content=text)], "loops": 0}


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


# ----- 3. batch_parse -----


def _parse_drafts(parser, text: str) -> list[dict]:
    """拆多笔草稿。嵌套数组的结构化输出偶发只回空对象，故按 schema 失败有限重试。"""
    messages: list = [
        SystemMessage(content=BILL_BATCH_SYSTEM),
        HumanMessage(content=text),
    ]
    for attempt in range(_BATCH_MAX_RETRIES + 1):
        try:
            batch = parser.invoke(messages)
            drafts = [d.model_dump() for d in batch.items if d.amount > 0][:_MAX_DRAFTS]
            if drafts:
                return drafts
            detail = "items 为空或金额缺失"
        except ValidationError as e:
            detail = str(e)[:200]
        except Exception as e:
            # 调用层失败（超时/网络等）：不可修复，直接放弃
            log_agent_exc("BILL_BATCH", e, input=text[:60])
            return []

        log_agent_exc(
            "BILL_BATCH",
            ValueError(f"invalid BillBatch attempt={attempt}: {detail}"),
            input=text[:60],
        )
        if attempt >= _BATCH_MAX_RETRIES:
            break
        messages.append(HumanMessage(content=BILL_BATCH_RETRY_HINT))
    return []


def make_batch_parse_node(model=llm):
    """把一句话拆成多笔草稿；未确认先出汇总卡片，确认后把草稿作为便签交给 bill_agent。"""
    parser = nested_structured_output(model, BillBatch)

    def batch_parse_node(state: BillAgentState) -> dict:
        text = _origin_text(state)
        drafts = _parse_drafts(parser, text)

        if not drafts:
            return {"result": {"success": False, "message": BATCH_EMPTY, "data": {}}}
        if not state.get("confirmed"):
            return {"drafts": drafts, "need_confirm": True}
        return {
            "drafts": drafts,
            "need_confirm": False,
            "messages": [
                SystemMessage(
                    content=BILL_BATCH_HINT.format(items=json.dumps(drafts, ensure_ascii=False))
                )
            ],
        }

    return batch_parse_node


# ----- 4. bill_agent -----


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

        text = _origin_text(state)
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
    """高危操作前输出确认卡片数据，等前端点确认/取消后续跑。"""
    intent = state.get("intent") or ""
    action = ACTION_LABEL.get(intent, "操作")

    if intent == "batch_create":
        rows = state.get("drafts") or []
        total = sum(float(d.get("amount") or 0) for d in rows)
        question = f"一共 {len(rows)} 笔，合计 {total:g} 元，确认都记下来吗？"
    else:
        candidates = state.get("candidates") or []
        target = state.get("target_bill") or {}
        rows = candidates or ([target] if target else [])
        if len(rows) > 1:
            question = f"找到 {len(rows)} 笔相近的账单，请点选要{action}的那一笔～"
        else:
            question = f"确认{action}这笔账单吗？"

    return {
        "messages": [AIMessage(content=question)],
        "result": {
            "success": True,
            "message": question,
            "data": {
                "need_confirm": True,
                "entity": "bill",
                "action": intent,
                "candidates": rows,
            },
        },
    }


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
