"""Open Task Router：在固定业务之上，判断是否为"开放式规划任务"。

不修改、不替代 Supervisor：Supervisor 仍只在 bill/analysis/budget 内路由。
本路由只负责把"综合规划类"请求识别为 open_planning，交给 CrewAI；其余一律回落，
由原 Supervisor 决策，保持固定业务链路不变。

两级判定：
1. is_probably_open：本地关键词/长度门控，只决定"要不要花一次 LLM"，不决定最终路由。
2. route_open_task：LLM + TaskRoute schema 校验；schema 失败有限重试（最多 2 次），
   仍失败再安全降级。网络/调用异常不重试，直接降级。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import log_agent_exc

_ALLOWED_TASK_TYPES = frozenset({"bill", "analysis", "budget", "open_planning"})
# 首次调用之外，schema 失败最多再试 2 次（可修复的模型输出错误，不是业务判断错误）
_MAX_SCHEMA_RETRIES = 2


class TaskRoute(BaseModel):
    """任务顶层路由：固定业务三选一，或开放式规划 open_planning。"""

    task_type: Literal["bill", "analysis", "budget", "open_planning"] = Field(
        description="bill/analysis/budget=固定业务；open_planning=综合/长周期规划报告",
    )
    reason: str = Field(default="", description="一句话分类依据")


_OPEN_HINTS = (
    "规划", "计划", "方案", "报告", "综合", "整体", "未来", "长期",
    "一年", "全年", "半年", "季度", "财富", "理财", "优化建议", "怎么规划",
    "如何安排", "帮我制定",
)

_OPEN_TASK_SYSTEM = """你是财务助手的任务分流器。判断用户请求是"固定业务"还是"开放式规划任务"。

- open_planning：需要综合分析 + 多步推理 + 产出规划/报告的开放任务。
  例：「根据我过去一年消费帮我制定财务规划」「给我一份综合财务分析报告」「帮我做未来一年的消费优化方案」「做个财富规划」
- bill / analysis / budget：单步、确定性的固定业务。
  例：记一笔账、查/改/删账单→bill；单项消费统计或趋势→analysis；设/查/看预算→budget

只能输出 task_type 为 bill / analysis / budget / open_planning 之一。
只有明确要"综合规划 / 多维报告 / 长期方案"时才选 open_planning；只要能被单个固定业务满足，就选对应的固定业务。"""

_RETRY_HINT = (
    "你的上一轮输出不符合要求。"
    "task_type 必须是：bill / analysis / budget / open_planning 之一，不能使用其他值。"
    "请重新判断，只输出符合 Schema 的结构化结果。"
)

_FALLBACK = TaskRoute(task_type="analysis", reason="fallback-non-open")


def is_probably_open(text: str) -> bool:
    """轻量门控：命中规划关键词、或较长的复合诉求，才值得进 LLM 判定。

    只做成本过滤，不决定最终业务路由：
    - False → 直接交给 Supervisor（零额外 LLM）
    - True  → 再调 LLM + schema 校验，才可能进 open_planning
    """
    t = text or ""
    if any(h in t for h in _OPEN_HINTS):
        return True
    return len(t) >= 18


def _validate_task_route(raw: Any) -> TaskRoute | None:
    """对 LLM 输出做严格 schema 校验，拦截幻觉/非法字段。"""
    try:
        if isinstance(raw, TaskRoute):
            route = raw
        elif isinstance(raw, dict):
            route = TaskRoute.model_validate(raw)
        elif hasattr(raw, "model_dump"):
            route = TaskRoute.model_validate(raw.model_dump())
        else:
            return None
    except (ValidationError, TypeError, ValueError):
        return None

    if route.task_type not in _ALLOWED_TASK_TYPES:
        return None
    return TaskRoute(task_type=route.task_type, reason=(route.reason or "")[:200])


def _schema_error_detail(raw: Any) -> str:
    """给重试提示附带上一轮非法内容摘要（截断，避免 prompt 膨胀）。"""
    try:
        if isinstance(raw, dict):
            text = str(raw)
        elif hasattr(raw, "model_dump"):
            text = str(raw.model_dump())
        else:
            text = repr(raw)
    except Exception:
        text = repr(raw)
    return text[:200]


def route_open_task(user_input: str, context: str = "") -> TaskRoute:
    """LLM 判定顶层任务类型。

    schema 校验失败：把错误反馈给 LLM，有限重试（最多 _MAX_SCHEMA_RETRIES 次）。
    调用异常（网络/超时等）：不重试，直接安全降级。
    重试耗尽：安全降级给 Supervisor。
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    human = user_input or ""
    if context:
        human = f"近期对话上下文：\n{context}\n\n当前用户说：{user_input or ''}"

    messages: list = [
        SystemMessage(content=_OPEN_TASK_SYSTEM),
        HumanMessage(content=human),
    ]
    router_llm = llm.with_structured_output(TaskRoute)

    for attempt in range(_MAX_SCHEMA_RETRIES + 1):
        decision: Any = None
        try:
            decision = router_llm.invoke(messages)
        except ValidationError as e:
            # structured_output 解析阶段的 schema 失败（如 task_type=financial_plan）→ 可重试
            decision = {"_parse_error": str(e)[:200]}
        except Exception as e:
            # 调用层失败（超时/网络等）：不是可修复的 schema 问题，不重试
            log_agent_exc("OPEN_ROUTER", e, input=(user_input or "")[:60])
            return _FALLBACK

        validated = _validate_task_route(decision)
        if validated is not None:
            return validated

        detail = _schema_error_detail(decision)
        log_agent_exc(
            "OPEN_ROUTER",
            ValueError(f"invalid TaskRoute attempt={attempt}: {detail}"),
            input=(user_input or "")[:60],
        )
        if attempt >= _MAX_SCHEMA_RETRIES:
            break
        # 仅对 schema 失败反馈重试：把非法输出和约束塞回对话
        messages.append(HumanMessage(content=f"{_RETRY_HINT}\n上一轮输出：{detail}"))

    return _FALLBACK


def is_open_planning(user_input: str, context: str = "") -> bool:
    """给 orchestrator 用的便捷判断：门控通过且 schema 校验后确认为 open_planning。"""
    if not is_probably_open(user_input):
        return False
    return route_open_task(user_input, context).task_type == "open_planning"
