"""Budget Workflow 节点。规则校验确定性；写读经 Tool，不碰 ORM。"""

from __future__ import annotations

import json
from datetime import date

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content, log_agent_exc

from .budget_prompt import (
    BUDGET_INTENT_SYSTEM,
    BUDGET_PARAM_SYSTEM,
    BUDGET_SYSTEM,
    INTENT_GUIDE,
    RESPONSE_SYSTEM,
)
from .budget_schemas import BudgetIntent, BudgetParams
from .budget_state import BudgetAgentState
from .budget_validator import validate_budget_params


# ----- 1. context_prepare -----


def context_prepare_node(state: BudgetAgentState) -> dict:
    text = (state.get("input") or "").strip()
    return {"messages": [HumanMessage(content=text)], "loops": 0, "need_input": False}


# ----- 2. intent_router -----


def make_intent_router_node(model=llm):
    router = model.with_structured_output(BudgetIntent)

    def budget_intent_router_node(state: BudgetAgentState) -> dict:
        if state.get("intent"):
            return {}
        text = state.get("input") or ""
        try:
            decision = router.invoke(
                [SystemMessage(content=BUDGET_INTENT_SYSTEM), HumanMessage(content=text)]
            )
            return {"intent": decision.intent}
        except Exception as e:
            log_agent_exc("BUDGET_INTENT", e, input=text[:60])
            return {"intent": "query_budget"}

    return budget_intent_router_node


# ----- 3. parameter_validator -----


def make_parameter_validator_node(model=llm):
    """先 LLM 抽参，再确定性 validate_budget_params。"""
    extractor = model.with_structured_output(BudgetParams)

    def parameter_validator_node(state: BudgetAgentState) -> dict:
        text = state.get("input") or ""
        intent = state.get("intent") or "query_budget"
        today = date.today()
        default_month = today.strftime("%Y-%m")
        default_year = today.strftime("%Y")

        try:
            raw = extractor.invoke(
                [
                    SystemMessage(
                        content=(
                            f"{BUDGET_PARAM_SYSTEM}\n"
                            f"今天：{today.isoformat()}；本月={default_month}；今年={default_year}；"
                            f"intent={intent}。"
                        )
                    ),
                    HumanMessage(content=text),
                ]
            )
            params = raw.model_dump()
        except Exception as e:
            log_agent_exc("BUDGET_PARAM", e, input=text[:60])
            params = {
                "amount": None,
                "period": default_month if intent != "set_budget" else None,
                "budget_type": "month",
                "is_total": True,
                "category": None,
            }

        # 查询/建议：缺 period 时默认本月
        if intent in ("query_budget", "budget_advice") and not (params.get("period") or "").strip():
            params["budget_type"] = params.get("budget_type") or "month"
            params["period"] = (
                default_year if params.get("budget_type") == "year" else default_month
            )

        result = validate_budget_params(intent, params)
        update: dict = {
            "budget_params": result["params"],
            "validation_result": result,
            "need_input": bool(result.get("need_input")),
        }
        if result.get("need_input"):
            msg = result["message"]
            update["messages"] = [AIMessage(content=msg)]
            update["final_response"] = msg
        return update

    return parameter_validator_node


# ----- 4. budget_policy_check -----


def make_budget_policy_check_node(tools_by_name: dict):
    """确定性层级检查：经 query_budget Tool，不让 LLM 判断，不直接 ORM。"""
    query_tool = tools_by_name["query_budget"]

    def budget_policy_check_node(state: BudgetAgentState) -> dict:
        intent = state.get("intent") or ""
        params = state.get("budget_params") or {}

        # 查询/建议不挡；年总预算是顶层也不挡
        if intent != "set_budget":
            return {"policy_result": {"ok": True, "message": ""}}

        budget_type = params.get("budget_type") or "month"
        period = params.get("period") or ""
        is_total = bool(params.get("is_total", True))

        if is_total and budget_type == "year":
            return {"policy_result": {"ok": True, "message": ""}}

        if is_total and budget_type == "month":
            year_period = period[:4]
            data = _tool_data(query_tool.invoke({"period": year_period, "budget_type": "year"}))
            # 年视图无显式年总时可能用月汇总顶数；用 categories 无关，看是否像「已设年总」
            # 保守：totalAmount<=0 视为未设年总
            if float(data.get("totalAmount") or 0) <= 0:
                return _policy_fail("请先设置年度总预算，再设本月总预算～")
            return {"policy_result": {"ok": True, "message": ""}}

        # 分类预算：对应周期须有总预算
        data = _tool_data(
            query_tool.invoke({"period": period, "budget_type": budget_type})
        )
        if float(data.get("totalAmount") or 0) <= 0:
            label = "月度" if budget_type == "month" else "年度"
            return _policy_fail(f"请先设置{label}总预算，再设分类预算～")
        return {"policy_result": {"ok": True, "message": ""}}

    return budget_policy_check_node


def _policy_fail(message: str) -> dict:
    return {
        "policy_result": {"ok": False, "message": message},
        "need_input": False,
        "messages": [AIMessage(content=message)],
        "final_response": message,
    }


def _tool_data(raw) -> dict:
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return {}
    if not isinstance(payload, dict) or not payload.get("success"):
        return {}
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


# ----- 5. budget_agent -----


def make_budget_agent_node(tools: list, model=llm):
    agent_llm = model.bind_tools(tools)

    def budget_agent_node(state: BudgetAgentState) -> dict:
        intent = state.get("intent") or "query_budget"
        params = state.get("budget_params") or {}
        guide = INTENT_GUIDE.get(intent, INTENT_GUIDE["query_budget"])
        hint = (
            f"{BUDGET_SYSTEM}\n\n{guide}\n"
            f"已校验参数：{json.dumps(params, ensure_ascii=False)}。"
            "请直接发起对应 tool call。"
            "涉及预算规则或是否合理时，可调用 search_finance_knowledge 检索规则依据。"
        )
        reply = agent_llm.invoke([SystemMessage(content=hint), *(state.get("messages") or [])])
        return {"messages": [reply], "loops": int(state.get("loops") or 0) + 1}

    return budget_agent_node


# ----- 7. response_generator -----


def make_response_generator_node(model=llm):
    def response_generator_node(state: BudgetAgentState) -> dict:
        if state.get("final_response"):
            return {}

        tool_payload = _latest_tool_payload(state.get("messages") or [])
        blob = json.dumps(
            {
                "intent": state.get("intent"),
                "budget_params": state.get("budget_params"),
                "tool_result": tool_payload,
            },
            ensure_ascii=False,
            default=str,
        )
        try:
            reply = extract_content(
                model.invoke(
                    [
                        SystemMessage(content=RESPONSE_SYSTEM),
                        HumanMessage(content=f"请根据下列数据回复用户：\n{blob[:3000]}"),
                    ]
                )
            ).strip()
        except Exception as e:
            log_agent_exc("BUDGET_RESPONSE", e)
            reply = _fallback_reply(tool_payload)

        if not reply:
            reply = _fallback_reply(tool_payload)
        return {
            "messages": [AIMessage(content=reply)],
            "tool_result": tool_payload,
            "final_response": reply,
        }

    return response_generator_node


def _latest_tool_payload(messages: list):
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            raw = msg.content
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except Exception:
                    return {"raw": raw}
            return raw
    return {}


def _fallback_reply(payload) -> str:
    if not payload:
        return "预算这边刚才没拿到结果，稍后再试一下～"
    if isinstance(payload, dict):
        if payload.get("success") is False:
            return payload.get("message") or "操作没成功，换个说法再试试～"
        data = payload.get("data") or {}
        if isinstance(data, dict) and "remaining" in data:
            rem = data.get("remaining")
            usage = data.get("usage_percent")
            hint = data.get("hint") or ""
            return hint or f"当前预算还剩 {rem} 元" + (f"，已用 {usage}%" if usage is not None else "")
        if payload.get("message"):
            return str(payload["message"])
    return "预算处理好了～"
