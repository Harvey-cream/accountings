"""Task Planner：把跨领域请求拆成多个 Domain Workflow 的执行计划。

定位（与另外两层路由的分工）：
- Supervisor：单域固定业务快速路由（bill/budget/asset/invoice 四选一），保持不变；
- Open Task Router：开放式规划与消费分析 → CrewAI，保持不变；
- Task Planner（本模块）：可由固定业务【组合】完成的跨域请求，
  如「工资8000记一笔，再更新工资卡余额」→ bill -> asset。

成本控制：is_probably_multi 先做确定性门控（命中 >=2 个业务域关键词组才调 LLM），
简单请求零额外 LLM 开销，仍走 Supervisor。
失败策略：schema/依赖校验失败有限重试；仍失败返回 None，由调用方回落 Supervisor。
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import log_agent_exc, nested_structured_output

from .task_schema import WorkflowPlan, topo_sort

_MAX_SCHEMA_RETRIES = 1

# 业务域关键词组：命中 >=2 组才视为"疑似跨域"，值得调一次 LLM 规划
_DOMAIN_HINTS = {
    "bill": ("记一笔", "记账", "帮我记", "账单", "改成", "删掉", "删除"),
    "budget": ("预算",),
    "asset": ("资产", "账户", "余额", "净资产", "负债", "存款", "银行卡", "信用卡", "进账"),
    "invoice": ("发票", "抬头", "税号", "开票"),
}

_PLANNER_SYSTEM = """你是财务任务规划器。你的职责不是回答用户，而是根据用户目标决定需要哪些业务 Workflow 协作，并给出依赖关系。

可用 Workflow（禁止创建不存在的类型）：
- bill：记一笔或多笔收支、查/改/删账单
- budget：预算的创建、查询、建议
- asset：资产账户与余额，总资产/净资产/负债，账户的增改删
- invoice：发票抬头、税号、开票信息的查询与增改删

规则：
1. 简单请求只返回一个任务。例：记账 → bill；查预算 → budget；查余额 → asset；查抬头 → invoice
2. 跨领域请求拆成多个任务并用 depends_on 表达先后。
   例：「发工资8000记一笔，顺便把工资卡余额加上」→ bill，asset(depends_on=[bill])
3. 每个任务的 goal 必须自包含：带上完成该任务所需的全部信息（金额、分类、账户名、时间范围等），后续任务不会再看到原始请求。
4. id 用简短英文且唯一；depends_on 只能引用已有任务 id；禁止循环依赖。
5. 宁可少拆，不要凑任务数：用户没提到的领域不要生成任务。
6. 你不调用数据库、不修改业务数据，只输出计划。

输出严格符合 WorkflowPlan Schema：tasks[].id / type / goal / depends_on。"""

_RETRY_HINT = (
    "你的上一轮输出不符合要求。"
    "type 必须是 bill / budget / asset / invoice 之一；id 必须唯一；"
    "depends_on 只能引用已有任务 id 且不得成环；tasks 不能为空。"
    "请重新规划，只输出符合 WorkflowPlan Schema 的结构化结果。"
)


def is_probably_multi(text: str) -> bool:
    """确定性门控：至少命中两个业务域的关键词才可能是跨域组合请求。"""
    t = text or ""
    groups = sum(1 for hints in _DOMAIN_HINTS.values() if any(h in t for h in hints))
    return groups >= 2


def _validate(raw: Any) -> WorkflowPlan | None:
    """严格校验：Pydantic 结构 + 依赖图可拓扑排序，失败返回 None。"""
    try:
        if isinstance(raw, WorkflowPlan):
            plan = raw
        elif isinstance(raw, dict):
            plan = WorkflowPlan.model_validate(raw)
        elif hasattr(raw, "model_dump"):
            plan = WorkflowPlan.model_validate(raw.model_dump())
        else:
            return None
    except (ValidationError, TypeError, ValueError):
        return None

    if topo_sort(plan) is None:
        return None
    return plan


def plan_workflows(user_input: str, context: str = "") -> WorkflowPlan | None:
    """产出跨 Workflow 执行计划；失败返回 None（调用方回落 Supervisor）。"""
    human = f"用户请求：{user_input or ''}"
    if context:
        human = f"近期对话上下文：\n{context}\n\n{human}"

    messages: list = [
        SystemMessage(content=_PLANNER_SYSTEM),
        HumanMessage(content=human),
    ]
    planner_llm = nested_structured_output(llm, WorkflowPlan)

    for attempt in range(_MAX_SCHEMA_RETRIES + 1):
        decision: Any = None
        try:
            decision = planner_llm.invoke(messages)
        except ValidationError as e:
            decision = {"_parse_error": str(e)[:200]}
        except Exception as e:
            # 调用层失败（超时/网络等）：不可修复，直接回落
            log_agent_exc("TASK_PLANNER", e, input=(user_input or "")[:60])
            return None

        plan = _validate(decision)
        if plan is not None:
            return plan

        log_agent_exc(
            "TASK_PLANNER",
            ValueError(f"invalid WorkflowPlan attempt={attempt}: {str(decision)[:200]}"),
            input=(user_input or "")[:60],
        )
        if attempt >= _MAX_SCHEMA_RETRIES:
            break
        messages.append(HumanMessage(content=_RETRY_HINT))

    return None
