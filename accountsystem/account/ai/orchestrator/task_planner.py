"""
Task Planner 模块
================================================================
作用：把"涉及多个固定业务域"的复合请求，拆成按依赖顺序执行的
      WorkflowPlan（任务计划），交给 executor.execute_plan 依序跑。

在顶层分流中的位置（第二层）：
  1) Open Task Router  → 开放分析/规划（CrewAI）
  2) Task Planner      → 跨域组合任务（本模块）
  3) Supervisor        → 单域固定业务（bill/budget/asset/invoice 四选一）

本模块做两件事：
  A. 门控：先判断这条请求"是不是跨域复合任务"（detect_multi_workflow）
  B. 规划：如果是，用 LLM 拆出多任务 + 依赖关系（plan_workflows）
================================================================
"""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, ValidationError

from account.ai.llm.llm import get_llm, llm
from account.ai.llm.llm_utils import log_agent_exc, nested_structured_output

from .task_schema import WorkflowPlan, topo_sort


# ============================================================
# 常量与 Prompt：LLM 行为的"说明书"
# ============================================================

# schema 失败最多再试 1 次
_MAX_SCHEMA_RETRIES = 1

# 业务域关键词组：命中 >=2 组时直接视为"疑似跨域"；否则再让轻量模型补判。
_DOMAIN_HINTS = {
    "bill": ("记一笔", "记账", "帮我记", "账单", "改成", "删掉", "删除"),
    "budget": ("预算",),
    "asset": ("资产", "账户", "余额", "净资产", "负债", "存款", "银行卡", "信用卡", "进账"),
    "invoice": ("发票", "抬头", "税号", "开票"),
}

# 规划器系统提示：告诉 LLM 怎么拆任务、怎么表达依赖
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

# 多域检测器系统提示：只判断"是不是同时涉及两个及以上固定业务域"，不拆具体任务
_MULTI_DETECT_SYSTEM = """你是财务任务识别器。你的职责不是回答用户，而是判断一个请求是否同时涉及多个固定业务域。

只允许识别四个业务域：
- bill：记账、收支、消费、收入、账单增删改查
- budget：预算设置、预算调整、预算查询、预算建议
- asset：资产账户、余额、银行卡、信用卡、净资产、负债
- invoice：发票抬头、税号、开票信息

要求：
1. 只输出结构化结果，不回答用户。
2. domains 只能从 bill / budget / asset / invoice 中选择，去重后按重要性排序。
3. 只有当请求明确同时涉及两个及以上业务域时，is_multi 才为 true。
4. 像“早饭20”“晚饭30”“消费30”“收入5000”这类自然语言记账应识别为 bill。
5. 不要因为“分析”“规划”之类宽泛词擅自加入 open_planning；这里只判断固定业务域。
"""

# schema 失败时，把错误提示塞回给 LLM 让它重来
_RETRY_HINT = (
    "你的上一轮输出不符合要求。"
    "type 必须是 bill / budget / asset / invoice 之一；id 必须唯一；"
    "depends_on 只能引用已有任务 id 且不得成环；tasks 不能为空。"
    "请重新规划，只输出符合 WorkflowPlan Schema 的结构化结果。"
)


# ============================================================
# 数据模型：LLM 输出的"合同"（结构化输出 Schema）
# ============================================================

class MultiTaskDecision(BaseModel):
    """
    多域探测结果：
      domains     - 命中哪些业务域（bill/budget/asset/invoice）
      is_multi    - 是否判定为跨域复合任务
      reason      - 判定依据（日志用）
    """
    domains: list[Literal["bill", "budget", "asset", "invoice"]] = Field(default_factory=list)
    is_multi: bool = False
    reason: str = ""


# ============================================================
# 门控层：先判断"是不是跨域任务"，决定要不要调深度 Planner
# ============================================================

def _keyword_domains(text: str) -> list[str]:
    """
    关键词硬匹配：看用户输入命中了哪些业务域的关键词组。
    命中 2 组以上时可以直接视为"疑似跨域"，省一次 LLM。
    """
    t = text or ""
    return [domain for domain, hints in _DOMAIN_HINTS.items() if any(h in t for h in hints)]


def detect_multi_workflow(text: str, context: str = "") -> MultiTaskDecision:
    """
    多域探测：两步走——
      1) 先关键词硬匹配，命中 >=2 个域直接判真
      2) 否则退回到 simple 档 LLM 做轻量结构化识别
    返回 MultiTaskDecision（domains + is_multi + reason）。
    """
    domains = _keyword_domains(text)
    if len(domains) >= 2:
        return MultiTaskDecision(domains=domains, is_multi=True, reason="keyword_multi")

    human = f"用户请求：{text or ''}"
    if context:
        human = f"近期对话上下文：\n{context}\n\n{human}"

    detector = get_llm("simple").with_structured_output(MultiTaskDecision)
    try:
        decision = detector.invoke(
            [SystemMessage(content=_MULTI_DETECT_SYSTEM), HumanMessage(content=human)]
        )
        if isinstance(decision, MultiTaskDecision):
            return decision
    except Exception as e:
        log_agent_exc("TASK_MULTI_DETECT", e, input=(text or "")[:60])
    return MultiTaskDecision(domains=domains, is_multi=False, reason="fallback_single")


def is_probably_multi(text: str, context: str = "") -> bool:
    """
    给 orchestrator 顶层分流用的便捷接口。
    返回 True 表示"值得调 plan_workflows 做深度规划"。
    """
    decision = detect_multi_workflow(text, context)
    return decision.is_multi and len(decision.domains) >= 2


# ============================================================
# 规划层：真正拆出 WorkflowPlan（任务 + 依赖）
# ============================================================

def _validate(raw: Any) -> WorkflowPlan | None:
    """
    严格校验 LLM 输出是否是合法 WorkflowPlan：
      - Pydantic 结构校验
      - 依赖图可拓扑排序（无重复 id / 无未知依赖 / 无循环依赖）
    校验失败返回 None，交给上层重试或回落。
    """
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
    """
    深度规划：调用大模型把复合请求拆成 WorkflowPlan。
      - schema 失败有限重试
      - 重试耗尽 / 调用异常 → 返回 None，由 orchestrator 回落 Supervisor
    """
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
