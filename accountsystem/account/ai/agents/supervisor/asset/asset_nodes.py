"""Asset Workflow 节点实现。节点只调 Tool，不碰 ORM。"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content, log_agent_exc

from .asset_prompt import (
    ACTION_LABEL,
    ASSET_DRAFT_HINT,
    ASSET_DRAFT_SYSTEM,
    ASSET_INTENT_SYSTEM,
    ASSET_LOCATOR_SYSTEM,
    ASSET_SYSTEM,
    ASSET_TARGET_HINT,
    DRAFT_INCOMPLETE,
    INTENT_GUIDE,
    NOT_FOUND,
    TARGET_AMBIGUOUS,
    TARGET_REQUIRED,
)
from .asset_schemas import AssetDraft, AssetIntent, AssetLocator
from .asset_state import AssetAgentState

_MAX_CANDIDATES = 5


def _draft_valid(draft: dict) -> bool:
    """新建账户草稿必须有 name 与 asset_type，否则不完整。"""
    return bool((draft or {}).get("name")) and bool((draft or {}).get("asset_type"))


def _origin_text(state: AssetAgentState) -> str:
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


def context_prepare_node(state: AssetAgentState) -> dict:
    """合并历史与本轮输入。结构化确认已由外壳写入 intent/target_account/confirmed。"""
    text = (state.get("input") or "").strip()
    return {"messages": [HumanMessage(content=text)], "loops": 0}


# ----- 2. intent_router -----


def make_intent_router_node(model=llm):
    """资产任务分类，只看文本，不访问数据库。"""
    router = model.with_structured_output(AssetIntent)

    def intent_router_node(state: AssetAgentState) -> dict:
        if state.get("intent"):
            return {}
        text = state.get("input") or ""
        try:
            decision = router.invoke(
                [SystemMessage(content=ASSET_INTENT_SYSTEM), HumanMessage(content=text)]
            )
            return {"intent": decision.intent}
        except Exception as e:
            log_agent_exc("ASSET_INTENT", e, input=text[:60])
            return {"intent": "query"}

    return intent_router_node


# ----- 3. asset_agent -----


def make_asset_agent_node(tools: list, model=llm):
    """按 intent 决定本轮该用哪些工具，由 LLM 发起 tool_calls。"""
    agent_llm = model.bind_tools(tools)

    def asset_agent_node(state: AssetAgentState) -> dict:
        guide = INTENT_GUIDE.get(state.get("intent") or "", "")
        system = SystemMessage(content=f"{ASSET_SYSTEM}\n\n{guide}".strip())
        reply = agent_llm.invoke([system, *(state.get("messages") or [])])
        return {"messages": [reply], "loops": int(state.get("loops") or 0) + 1}

    return asset_agent_node


# ----- 4. mutation_check -----


def make_mutation_check_node(tools_by_name: dict, model=llm):
    """写操作前先确认对象：新建看草稿，改删调整先定位账户。"""
    locator = model.with_structured_output(AssetLocator)
    drafter = model.with_structured_output(AssetDraft)
    search_tool = tools_by_name["search_asset_accounts"]

    def mutation_check_node(state: AssetAgentState) -> dict:
        text = _origin_text(state)

        if (state.get("intent") or "") == "create":
            if state.get("confirmed"):
                draft = state.get("draft") or {}
                if not _draft_valid(draft):
                    return {
                        "result": {"success": False, "message": DRAFT_INCOMPLETE, "data": {"needs_input": True}}
                    }
                return {
                    "need_confirm": False,
                    "messages": [
                        SystemMessage(
                            content=ASSET_DRAFT_HINT.format(
                                draft=json.dumps(draft, ensure_ascii=False)
                            )
                        )
                    ],
                }
            try:
                draft = drafter.invoke(
                    [SystemMessage(content=ASSET_DRAFT_SYSTEM), HumanMessage(content=text)]
                ).model_dump()
            except Exception as e:
                log_agent_exc("ASSET_DRAFT", e, input=text[:60])
                draft = {}
            # 草稿不完整（含 LLM 失败的空草稿）绝不进入确认/新建，直接询问
            if not _draft_valid(draft):
                return {
                    "result": {"success": False, "message": DRAFT_INCOMPLETE, "data": {"needs_input": True}}
                }
            return {"draft": draft, "need_confirm": True}

        target = state.get("target_account") or {}
        if target.get("id"):
            return _located(state, target)

        try:
            hint = locator.invoke(
                [SystemMessage(content=ASSET_LOCATOR_SYSTEM), HumanMessage(content=text)]
            )
        except Exception as e:
            log_agent_exc("ASSET_LOCATOR", e, input=text[:60])
            hint = AssetLocator()

        if hint.account_id:
            return _located(state, {"id": hint.account_id})

        name = hint.name
        if not name:
            # Locator 未给出可用条件：用 Planner 显式定位字段做安全 fallback；
            # 仍无则停下询问，绝不做空条件搜索来自动选中账户
            ti = state.get("task_input") or {}
            if ti.get("account_id"):
                return _located(state, {"id": int(ti["account_id"])})
            name = ti.get("name")
            if not name:
                return {
                    "result": {"success": False, "message": TARGET_REQUIRED, "data": {"needs_input": True}}
                }

        rows = _tool_rows(
            search_tool.invoke({"name": name, "limit": _MAX_CANDIDATES})
        )
        if not rows:
            return {
                "result": {"success": False, "message": NOT_FOUND, "data": {"needs_input": True}}
            }
        if len(rows) == 1:
            return _located(state, rows[0], candidates=rows)
        # 多条命中：目标不唯一，停下让用户说具体点，绝不自动选中（NEED_SELECTION）
        return {
            "result": {
                "success": False,
                "message": TARGET_AMBIGUOUS,
                "data": {"needs_input": True, "candidates": rows[:_MAX_CANDIDATES]},
            }
        }

    return mutation_check_node


def _located(state: AssetAgentState, target: dict, candidates: list | None = None) -> dict:
    """唯一命中：已确认就带着 id 去执行，未确认就先问一句。"""
    update: dict = {"target_account": target, "need_confirm": not state.get("confirmed")}
    if candidates:
        update["candidates"] = candidates
    if state.get("confirmed"):
        update["messages"] = [
            SystemMessage(
                content=ASSET_TARGET_HINT.format(account=json.dumps(target, ensure_ascii=False))
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


def human_confirm_node(state: AssetAgentState) -> dict:
    """写操作前输出确认卡片数据，等前端点确认/取消后续跑。"""
    intent = state.get("intent") or ""
    action = ACTION_LABEL.get(intent, "操作")

    if intent == "create":
        draft = state.get("draft") or {}
        name = draft.get("name") or "新账户"
        question = f"确认{action}账户「{name}」吗？"
        rows = [draft] if draft else []
    else:
        candidates = state.get("candidates") or []
        target = state.get("target_account") or {}
        rows = candidates or ([target] if target else [])
        if len(rows) > 1:
            question = f"找到 {len(rows)} 个相近的账户，请点选要{action}的那一个～"
        else:
            question = f"确认{action}这个账户吗？"

    return {
        "messages": [AIMessage(content=question)],
        "result": {
            "success": True,
            "message": question,
            "data": {
                "need_confirm": True,
                "entity": "asset",
                "action": intent,
                "candidates": rows,
            },
        },
    }


# ----- 6. result_formatter -----


def result_formatter_node(state: AssetAgentState) -> dict:
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
                "target_account": state.get("target_account"),
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
