"""Unified top-level planner for single, multi, and open tasks."""

from __future__ import annotations

from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage
from openai import APIConnectionError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from account.ai.llm.llm import planner_llm
from account.ai.llm.llm_utils import log_agent_exc, nested_structured_output

from .task_schema import WorkflowPlan, topo_sort


_MAX_SCHEMA_RETRIES = 2

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
1. 单域请求输出一个 Task，复合请求输出多个 Task；每个 Task 必须同时提供 id、type、action 和 action 对应的 input。
2. action 是 Task 一级字段，严禁放入 input；input 只能包含该 action 的真实业务字段，禁止额外字段。
3. goal 必须只描述这一个 Task 自身要达成什么，用一句中文说清；严禁把整句用户请求、也不要提及别的 Task 的目标（复合请求里每个 Task 各说各的）。
4. Bill create 使用 amount/category/date/description/bill_type，batch_create 使用 items；query 使用 keyword/category/exclude_category/period/date/start_date/end_date/days/bill_type/limit；update/delete 可以提供真实 bill_id，也可以只提供 keyword/category/date/days/bill_type 等定位条件，由 Bill Workflow 自己查询和处理候选。period 用 YYYY-MM 或 YYYY，date 用 YYYY-MM-DD。禁止字符串模板、占位符或虚构 ID。
5. Budget set_budget 使用 amount/period/budget_type/is_total/category；query_budget/budget_advice 使用 period/budget_type；预算没有 delete action。用户未指明预算周期时按默认处理：budget_type=month，period 取上方「今天」所在月份（YYYY-MM）。
6. Asset create 使用 name/asset_type/balance/account_type/is_included_in_total/remark；query 使用 account_id/name；update 使用 keyword/account_id 定位 + 要改的字段（name/asset_type/balance/account_type/is_included_in_total/remark），其中「改成/设为某个余额」用 balance（绝对值），「进账/花了/减少」用 adjust_balance 的 delta（增量）；delete 使用 keyword/account_id。只有用户明确报了账户编号才填 account_id，否则一律用 keyword 描述账户名，由 Asset Workflow 自己定位。
7. Invoice create 使用 name/tax_id/amount/address/phone/bank/account/remark；query 使用 invoice_id/keyword；update 使用 keyword/invoice_id 定位 + 要改的字段；delete 使用 keyword/invoice_id。同资产域：没有明确编号就只给 keyword，由 Invoice Workflow 自己定位。
8. open_planning 仅用于统计、趋势、综合推理或规划报告，使用 analyze 和 topic。
9. 只有确实需要前一个 Task 完成后才能执行下一个 Task 时才填写 depends_on；depends_on 只表达执行顺序，不表达业务目标或业务 ID 解析。查询到零条或多条候选时，不得自动选择。
10. 用户意图明确但参数不全（例如只说「帮我记一笔」没说金额、只说「新建一个账户」没说类型）时，仍按意图输出对应 Task，缺的字段就留空——由该 Workflow 停下来追问用户。严禁因为缺参数就把业务请求降级成 query 或 chat。
11. 只输出符合 WorkflowPlan schema 的结构化 Plan，不回答用户。
12. 只有明确的记账、查账单、预算、资产、发票操作才路由到对应 Workflow；纯聊天/闲聊/概念性知识问答才走 chat.respond。禁止让 chat 代替业务 Workflow，例如「查最近一个月的账单」必须是 bill.query，不能路由到 chat。"""


def _planner_system() -> str:
    """规划器系统提示：注入当前日期，供相对周期（本月 / 今年）解析。"""
    today = date.today()
    return (
        f"{_PLANNER_SYSTEM}\n\n"
        f"今天：{today.isoformat()}（本月={today.strftime('%Y-%m')}，今年={today.strftime('%Y')}）。"
    )


def build_route_plan(user_input: str, context: str = "") -> WorkflowPlan:
    """产出 WorkflowPlan。失败时抛 PlannerError 子类（自带面向用户文案）。

    仅结构化输出 / schema 校验失败重试一次；超时 / 连接 / 限流直接快速失败。
    """
    human = f"用户请求：{user_input or ''}"
    if context:
        human = f"近期对话上下文：\n{context}\n\n{human}"
    planner = nested_structured_output(planner_llm, WorkflowPlan)
    messages = [SystemMessage(content=_planner_system()), HumanMessage(content=human)]
    for attempt in range(_MAX_SCHEMA_RETRIES + 1):
        try:
            result = planner.invoke(messages)
            if result is None:
                # 模型未产出 tool call 时 structured_output 返回 None 而非抛异常；
                # 显式转成可重试的结构化输出失败，避免落到 model_validate(None) 的假象报错。
                raise ValueError("planner returned no structured output")
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
