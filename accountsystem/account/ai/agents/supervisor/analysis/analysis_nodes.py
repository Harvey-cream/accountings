"""Analysis Workflow 节点。节点只调 Tool，不碰 ORM。"""

from __future__ import annotations

import json
from datetime import date

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content, log_agent_exc

from .analysis_prompt import (
    ANALYSIS_INTENT_SYSTEM,
    ANALYSIS_PARAM_SYSTEM,
    ANALYSIS_SYSTEM,
    INSIGHT_SYSTEM,
    INTENT_GUIDE,
)
from .analysis_schemas import AnalysisIntent, AnalysisParams
from .analysis_state import AnalysisAgentState


# ----- 1. context_prepare -----


def context_prepare_node(state: AnalysisAgentState) -> dict:
    """合并历史与本轮输入；不调工具、不查库。"""
    text = (state.get("input") or "").strip()
    return {"messages": [HumanMessage(content=text)], "loops": 0}


# ----- 2. intent_router -----


def make_intent_router_node(model=llm):
    router = model.with_structured_output(AnalysisIntent)

    def analysis_intent_router_node(state: AnalysisAgentState) -> dict:
        if state.get("intent"):
            return {}
        text = state.get("input") or ""
        try:
            decision = router.invoke(
                [SystemMessage(content=ANALYSIS_INTENT_SYSTEM), HumanMessage(content=text)]
            )
            return {"intent": decision.intent}
        except Exception as e:
            log_agent_exc("ANALYSIS_INTENT", e, input=text[:60])
            return {"intent": "summary"}

    return analysis_intent_router_node


# ----- 3. parameter_normalize -----


def make_parameter_normalize_node(model=llm):
    """自然语言 → days/category；工具未改，日期区间只作标签，days 喂给 Tool。"""
    extractor = model.with_structured_output(AnalysisParams)

    def parameter_normalize_node(state: AnalysisAgentState) -> dict:
        text = state.get("input") or ""
        intent = state.get("intent") or "summary"
        today = date.today()
        month_days = today.day

        try:
            raw = extractor.invoke(
                [
                    SystemMessage(
                        content=(
                            f"{ANALYSIS_PARAM_SYSTEM}\n"
                            f"当前日期：{today.isoformat()}；本月已过天数：{month_days}；"
                            f"已判定 intent={intent}。"
                        )
                    ),
                    HumanMessage(content=text),
                ]
            )
        except Exception as e:
            log_agent_exc("ANALYSIS_PARAM", e, input=text[:60])
            raw = AnalysisParams(days=30, period_label="近30天")

        params = raw.model_dump()
        params["days"] = max(1, min(int(params.get("days") or 30), 365))

        if intent == "category" and not (params.get("category") or "").strip():
            params["need_input"] = True
            params["ask_message"] = params.get("ask_message") or "想看哪个分类的消费呀？比如餐饮、交通～"
        elif params.get("need_input") and not (params.get("ask_message") or "").strip():
            params["ask_message"] = "请告诉我需要分析哪个时间范围～"

        if not params.get("period_label"):
            params["period_label"] = f"近{params['days']}天"

        # 为本月场景补展示用起止日（工具仍只用 days）
        if params.get("period_label") == "本月" and not params.get("start_date"):
            params["start_date"] = today.replace(day=1).isoformat()
            params["end_date"] = today.isoformat()
            params["days"] = month_days

        update: dict = {"parameters": params}
        if params.get("need_input"):
            ask = params["ask_message"]
            update["messages"] = [AIMessage(content=ask)]
            update["final_response"] = ask
        return update

    return parameter_normalize_node


# ----- 4. analysis_agent -----


def make_analysis_agent_node(tools: list, model=llm):
    agent_llm = model.bind_tools(tools)

    def analysis_agent_node(state: AnalysisAgentState) -> dict:
        intent = state.get("intent") or "summary"
        params = state.get("parameters") or {}
        guide = INTENT_GUIDE.get(intent, INTENT_GUIDE["summary"])
        hint = (
            f"{ANALYSIS_SYSTEM}\n\n{guide}\n"
            f"已归一化参数：days={params.get('days', 30)}, "
            f"category={params.get('category')!r}, "
            f"period_label={params.get('period_label')!r}。"
            "请直接按上述参数发起对应 tool call，不要追问。"
            "如需给出消费优化建议，可再调用 search_finance_knowledge 检索内部知识作为依据。"
        )
        reply = agent_llm.invoke([SystemMessage(content=hint), *(state.get("messages") or [])])
        return {"messages": [reply], "loops": int(state.get("loops") or 0) + 1}

    return analysis_agent_node


# ----- 6. insight_generate -----


def make_insight_generate_node(model=llm):
    def insight_generate_node(state: AnalysisAgentState) -> dict:
        if state.get("final_response"):
            return {}

        params = state.get("parameters") or {}
        tool_payload = _latest_tool_payload(state.get("messages") or [])
        blob = json.dumps(
            {
                "intent": state.get("intent"),
                "parameters": {
                    "days": params.get("days"),
                    "category": params.get("category"),
                    "period_label": params.get("period_label"),
                    "start_date": params.get("start_date"),
                    "end_date": params.get("end_date"),
                },
                "tool_result": tool_payload,
            },
            ensure_ascii=False,
            default=str,
        )
        try:
            reply = extract_content(
                model.invoke(
                    [
                        SystemMessage(content=INSIGHT_SYSTEM),
                        HumanMessage(content=f"请根据下列数据生成洞察：\n{blob[:3000]}"),
                    ]
                )
            ).strip()
        except Exception as e:
            log_agent_exc("ANALYSIS_INSIGHT", e)
            reply = _fallback_insight(tool_payload)

        if not reply:
            reply = _fallback_insight(tool_payload)
        return {
            "messages": [AIMessage(content=reply)],
            "tool_result": tool_payload,
            "final_response": reply,
        }

    return insight_generate_node


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


def _fallback_insight(payload) -> str:
    if not payload:
        return "刚才没拿到分析数据，换个时间范围再说一次呗～"
    if isinstance(payload, dict) and payload.get("success") is False:
        return payload.get("message") or "分析失败了，稍后再试试～"
    if isinstance(payload, dict) and payload.get("message"):
        data = payload.get("data")
        if isinstance(data, dict) and data.get("summary"):
            return str(data["summary"])
        return str(payload["message"])
    return "分析好了，细节可以再问我哦～"
