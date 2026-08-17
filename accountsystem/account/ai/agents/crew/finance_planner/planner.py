"""Task Planner：根据用户目标决定本次需要哪些角色，动态产出任务计划。

用项目统一的 LLM + 结构化输出（与 supervisor / open_task_router 同构），
不额外起一个 CrewAI Agent：规划发生在建 Crew 之前，省一轮 kickoff。

失败策略：schema 校验失败有限重试；仍失败则回落到原固定三步计划，
保证 Crew 始终有可执行的 plan（整体异常由 crew.py 统一降级）。
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import log_agent_exc, nested_structured_output

from . import prompts
from .planner_schema import ROLE_KEYS, TaskPlan, TaskSpec

_MAX_SCHEMA_RETRIES = 1
_ADVISOR = "financial_advisor"


def _default_plan() -> list[TaskSpec]:
    """Planner 不可用时的兜底：原有的分析 -> 预算 -> 顾问三步。"""
    return _normalize(
        [
            TaskSpec(role="financial_analyst", goal="分析用户的消费结构与趋势"),
            TaskSpec(role="budget_planner", goal="据分析结论提出预算规划方案"),
            TaskSpec(role=_ADVISOR, goal="综合前序结论生成最终财务建议"),
        ]
    )


def _normalize(specs: list[TaskSpec]) -> list[TaskSpec]:
    """角色去重、补默认产出、强制 financial_advisor 收尾。"""
    ordered: list[TaskSpec] = []
    seen: set[str] = set()
    for spec in specs:
        if spec.role not in ROLE_KEYS or spec.role in seen or spec.role == _ADVISOR:
            continue
        seen.add(spec.role)
        ordered.append(
            TaskSpec(
                role=spec.role,
                goal=(spec.goal or "").strip() or prompts.ROLE_PROFILES[spec.role]["goal"],
                expected_output=(spec.expected_output or "").strip()
                or prompts.DEFAULT_EXPECTED_OUTPUT[spec.role],
            )
        )

    # 顾问始终存在且排在最后：保证产出可被 CrewResult 约束
    advisor = next((s for s in specs if s.role == _ADVISOR), None)
    ordered.append(
        TaskSpec(
            role=_ADVISOR,
            goal=(getattr(advisor, "goal", "") or "").strip() or "综合前序结论生成最终财务建议",
            expected_output=(getattr(advisor, "expected_output", "") or "").strip()
            or prompts.DEFAULT_EXPECTED_OUTPUT[_ADVISOR],
        )
    )
    return ordered


def _validate(raw: Any) -> list[TaskSpec] | None:
    """严格校验 Planner 输出，拦截幻觉角色/空计划。"""
    try:
        if isinstance(raw, TaskPlan):
            plan = raw
        elif isinstance(raw, dict):
            plan = TaskPlan.model_validate(raw)
        elif hasattr(raw, "model_dump"):
            plan = TaskPlan.model_validate(raw.model_dump())
        else:
            return None
    except (ValidationError, TypeError, ValueError):
        return None

    # 只有顾问一人（或全是非法角色）说明没规划出实质工作，判为失败
    workers = [s for s in plan.tasks if s.role in ROLE_KEYS and s.role != _ADVISOR]
    if not workers:
        return None
    return _normalize(plan.tasks)


def plan_tasks(user_input: str, history_text: str = "") -> list[TaskSpec]:
    """产出本次要执行的任务计划；任何失败都回落到默认三步计划。"""
    human = f"用户诉求：{user_input or ''}"
    if history_text:
        human = f"近期对话上下文：\n{history_text}\n\n{human}"

    messages: list = [
        SystemMessage(content=prompts.PLANNER_SYSTEM),
        HumanMessage(content=human),
    ]
    planner_llm = nested_structured_output(llm, TaskPlan)

    for attempt in range(_MAX_SCHEMA_RETRIES + 1):
        decision: Any = None
        try:
            decision = planner_llm.invoke(messages)
        except ValidationError as e:
            decision = {"_parse_error": str(e)[:200]}
        except Exception as e:
            log_agent_exc("CREW_PLANNER", e, input=(user_input or "")[:60])
            return _default_plan()

        specs = _validate(decision)
        if specs:
            return specs

        log_agent_exc(
            "CREW_PLANNER",
            ValueError(f"invalid TaskPlan attempt={attempt}: {str(decision)[:200]}"),
            input=(user_input or "")[:60],
        )
        if attempt >= _MAX_SCHEMA_RETRIES:
            break
        messages.append(HumanMessage(content=prompts.PLANNER_RETRY_HINT))

    return _default_plan()
