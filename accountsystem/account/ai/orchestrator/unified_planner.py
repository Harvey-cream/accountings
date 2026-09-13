"""Unified top-level planner for single, multi, and open tasks."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from openai import APIConnectionError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from account.ai.llm.llm import planner_llm
from account.ai.llm.llm_utils import log_agent_exc, nested_structured_output

from .task_schema import WorkflowPlan, topo_sort


_MAX_SCHEMA_RETRIES = 1

# Compatibility name for callers that have not migrated imports yet. The
# Planner and executor use WorkflowPlan itself as the authoritative schema.
RoutePlan = WorkflowPlan


# ============================================================
# Planner 失败类型：每种故障携带明确的面向用户提示
# ============================================================

class PlannerError(Exception):
    """Planner 失败的统一基类，携带面向用户的提示文案。"""

    kind = "unknown"
    user_message = "暂时无法生成有效的执行计划，请换一种说法再试试。"


class PlannerTimeout(PlannerError):
    kind = "timeout"
    user_message = "服务响应有点慢，请稍后再试。"


class PlannerUnavailable(PlannerError):
    kind = "connection"
    user_message = "AI 服务暂时不可用，请稍后再试。"


class PlannerRateLimited(PlannerError):
    kind = "rate_limit"
    user_message = "当前请求较多，请稍后再试。"


class PlannerStructuredOutputError(PlannerError):
    kind = "structured_output"
    user_message = "暂时无法理解这次请求，请稍后再试。"


_ERROR_BY_KIND = {
    "timeout": PlannerTimeout,
    "connection": PlannerUnavailable,
    "rate_limit": PlannerRateLimited,
    "structured_output": PlannerStructuredOutputError,
    "unknown": PlannerError,
}

# 只有结构化输出 / schema 校验失败才允许应用层 schema 纠正重试；
# 超时 / 连接 / 限流快速失败，不做 schema retry。
_RETRYABLE_KINDS = frozenset({"structured_output"})

_RETRY_HINT = "上一次输出未通过校验，请修正后重试。具体校验错误：{error}"


def classify_planner_error(exc: BaseException) -> str:
    """归类 Planner 异常（基于 SDK 异常类，不做字符串匹配）。

    APITimeoutError 是 APIConnectionError 的子类，必须先判 timeout。
    """
    if isinstance(exc, APITimeoutError):
        return "timeout"
    if isinstance(exc, APIConnectionError):
        return "connection"
    if isinstance(exc, RateLimitError):
        return "rate_limit"
    if isinstance(exc, (ValidationError, ValueError, TypeError)):
        return "structured_output"
    return "unknown"


_PLANNER_SYSTEM = """你是财务助手的统一顶层规划器。一次理解用户请求，并输出一个包含一个或多个 Task 的 Plan。

可用 Task 类型与 action：
- bill：create、batch_create、query、update、delete
- budget：set_budget、query_budget、budget_advice
- asset：create、query、update、delete、adjust_balance
- invoice：create、query、update、delete
- open_planning：analyze
- chat：respond（普通聊天、寒暄之外的闲聊、概念性财务知识问答），input 用 message 字段

规则：
1. 单域请求输出一个 Task，复合请求输出多个 Task；每个 Task 必须同时提供 type、action 和 action 对应的完整 input。
2. action 是 Task 一级字段，严禁放入 input；input 只能包含该 action 的真实业务字段，禁止额外字段。
3. Bill create 使用 amount/category/date/description/bill_type，batch_create 使用 items，query/update/delete 使用真实业务字段和目标描述；update/delete 可以提供真实 bill_id，也可以只提供 keyword/category/date/days/bill_type 等定位条件，由 Bill Workflow 自己查询和处理候选。禁止字符串模板、占位符或虚构 ID。
4. Budget set_budget 使用 amount/period/budget_type/is_total/category；query_budget/budget_advice 使用 period/budget_type；预算没有 delete action。
5. Asset create 使用 name/asset_type/balance/account_type/is_included_in_total/remark，query 使用 account_id/name，update/delete 需真实 account_id，adjust_balance 需 account_id/delta。
6. Invoice create 使用发票抬头字段，query 使用 invoice_id/keyword，update/delete 需 invoice_id。
7. open_planning 仅用于统计、趋势、综合推理或规划报告，使用 analyze 和 topic。
8. 只有确实需要前一个 Task 完成后才能执行下一个 Task 时才填写 depends_on；depends_on 只表达执行顺序，不表达业务目标或业务 ID 解析。查询到零条或多条候选时，不得自动选择。
9. 只输出符合 WorkflowPlan schema 的结构化 Plan，不回答用户。
10. 只有明确的记账、查账单、预算、资产、发票操作才路由到对应 Workflow；纯聊天/闲聊/概念性知识问答才走 chat.respond。禁止让 chat 代替业务 Workflow，例如「查最近一个月的账单」必须是 bill.query，不能路由到 chat。"""


def build_route_plan(user_input: str, context: str = "") -> WorkflowPlan:
    """产出 WorkflowPlan。失败时抛 PlannerError 子类（自带面向用户文案）。

    仅结构化输出 / schema 校验失败重试一次；超时 / 连接 / 限流直接快速失败。
    """
    human = f"用户请求：{user_input or ''}"
    if context:
        human = f"近期对话上下文：\n{context}\n\n{human}"
    planner = nested_structured_output(planner_llm, WorkflowPlan)
    messages = [SystemMessage(content=_PLANNER_SYSTEM), HumanMessage(content=human)]
    for attempt in range(_MAX_SCHEMA_RETRIES + 1):
        try:
            result = planner.invoke(messages)
            plan = (
                result
                if isinstance(result, WorkflowPlan)
                else WorkflowPlan.model_validate(
                    result.model_dump() if hasattr(result, "model_dump") else result
                )
            )
            if topo_sort(plan) is None:
                raise ValueError("workflow plan contains invalid dependencies")
            return plan
        except Exception as exc:
            kind = classify_planner_error(exc)
            log_agent_exc(
                "UNIFIED_PLANNER", exc, kind=kind, input=(user_input or "")[:60], attempt=attempt
            )
            if kind not in _RETRYABLE_KINDS or attempt >= _MAX_SCHEMA_RETRIES:
                raise _ERROR_BY_KIND[kind]() from exc
            messages.append(HumanMessage(content=_RETRY_HINT.format(error=str(exc)[:2000])))
    raise PlannerError()
