"""Unified top-level planner for single, multi, and open tasks."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import log_agent_exc, nested_structured_output

from .task_schema import WorkflowPlan, topo_sort


_MAX_SCHEMA_RETRIES = 1

# Compatibility name for callers that have not migrated imports yet. The
# Planner and executor use WorkflowPlan itself as the authoritative schema.
RoutePlan = WorkflowPlan


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


def build_route_plan(user_input: str, context: str = "") -> WorkflowPlan | None:
    human = f"用户请求：{user_input or ''}"
    if context:
        human = f"近期对话上下文：\n{context}\n\n{human}"
    planner = nested_structured_output(llm, WorkflowPlan)
    messages = [SystemMessage(content=_PLANNER_SYSTEM), HumanMessage(content=human)]
    last_error = ""
    for attempt in range(_MAX_SCHEMA_RETRIES + 1):
        try:
            result = planner.invoke(messages)
            if isinstance(result, WorkflowPlan):
                if topo_sort(result) is None:
                    raise ValueError("workflow plan contains invalid dependencies")
                return result
            return WorkflowPlan.model_validate(result.model_dump() if hasattr(result, "model_dump") else result)
        except (ValidationError, ValueError, TypeError) as exc:
            last_error = str(exc)
            log_agent_exc("UNIFIED_PLANNER", exc, input=(user_input or "")[:60], attempt=attempt)
        except Exception as exc:
            last_error = str(exc)
            log_agent_exc("UNIFIED_PLANNER", exc, input=(user_input or "")[:60], attempt=attempt)
        if attempt < _MAX_SCHEMA_RETRIES:
            messages.append(HumanMessage(content=f"上一次输出未通过校验，请修正后重试。具体校验错误：{last_error[:2000]}"))
    return None
