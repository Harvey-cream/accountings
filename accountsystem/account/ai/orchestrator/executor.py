"""
Executor 执行层模块
================================================================
作用：根据 orchestrator 分流定下的 task_type，真正调用业务 Agent 执行业务，
      并把结果统一写回 state.final_response。

本模块做两件事：
  A. execute()      —— 单任务执行（bill / budget / asset / invoice / open_planning）
  B. execute_plan() —— 跨域计划执行（Task Planner 拆出的多 Workflow，按依赖序跑）

execute_plan 有两种行为模式：
  - 预览模式（未确认）：多任务且含写操作时，先出"计划级确认卡"，不真正执行
  - 执行模式（已确认）：用户点确认后（confirmed_plan=True），才依序真正跑 Workflow

输出形状统一为 {output, intermediate_steps[, confirm][, plan_tasks]}，
供 to_api_dict / SSE / 消息落库复用。
================================================================
"""

from __future__ import annotations

import re

from account.ai.agents.crew.finance_planner import run_finance_planner
from account.ai.agents.supervisor import asset, bill, budget, invoice

from .state import AgentState
from .task_schema import WorkflowPlan, topo_sort


# ============================================================
# 常量：业务映射与执行参数
# ============================================================

# task_type → 对应业务 Agent.run 的映射表
_RUNNERS = {
    "bill": bill.run,
    "budget": budget.run,
    "asset": asset.run,
    "invoice": invoice.run,
}

# 带 human_confirm 机制、能接收确认卡片回传的业务域
_CONFIRM_TASKS = frozenset({"bill", "asset", "invoice"})

# 前序任务结果注入下一任务时的最大字符数，防止 prompt 无限膨胀
_PREV_RESULT_MAX_CHARS = 800


# ============================================================
# 单任务执行：交给某个业务 Agent 跑一次
# ============================================================

def execute(state: AgentState) -> AgentState:
    """
    单任务执行：
      - open_planning → 交给 CrewAI 协作节点（Finance Planner）
      - 其他 → 从 _RUNNERS 查对应业务 Agent（bill/budget/asset/invoice）
    结果写回 state.tool_results 和 state.final_response。
    """
    task = state.get("task_type") or "bill"

    # 开放式规划任务：交给 CrewAI 协作节点（不走 LangGraph Workflow）
    if task == "open_planning":
        result = run_finance_planner(
            state.get("user_input") or "",
            state.get("user"),
            history=state.get("memory_messages") or [],
        )
        state["tool_results"] = result.get("intermediate_steps") or []
        state["final_response"] = result
        return state

    runner = _RUNNERS.get(task, bill.run)
    kwargs = {
        "history": state.get("memory_messages") or [],
    }
    if task in _CONFIRM_TASKS and state.get("confirm") is not None:
        kwargs["confirm"] = state.get("confirm")
    result = runner(state.get("user_input") or "", state.get("user"), **kwargs)
    state["tool_results"] = result.get("intermediate_steps") or []
    state["final_response"] = result
    return state


# ============================================================
# 跨计划辅助函数：上下文拼装 + 预览数据提取
# ============================================================

def _task_input(task, results: dict, multi: bool, user_input: str) -> str:
    """
    组装某个子任务的输入文本：
      - 多任务场景：用 task.goal（自包含目标），避免其他域的诉求干扰
      - 单任务场景：直接用原始 user_input，避免 goal 里丢失细节
      - 有依赖时，把前序任务的 output 截断后附加进去，作为上下文
    """
    text = (task.goal or "").strip() if multi else ""
    text = text or user_input
    prev = [
        (results[dep].get("output") or "").strip()
        for dep in task.depends_on
        if dep in results
    ]
    prev = [p for p in prev if p]
    if prev:
        joined = "\n\n".join(p[:_PREV_RESULT_MAX_CHARS] for p in prev)
        text = f"{text}\n\n参考前序任务结果：\n{joined}"
    return text


def _extract_bill_candidates(goal: str) -> list[dict]:
    """
    从 bill 任务的 goal 文本里，用正则抠出"名称+金额"对，
    生成账单候选列表（用于确认卡预览，不落库）。
    会过滤掉名称里含"预算/余额/资产/发票"的干扰匹配。
    """
    pattern = re.compile(r"([一-龥A-Za-z]+?)(\d+(?:\.\d+)?)元?")
    candidates = []
    for name, amount in pattern.findall(goal or ""):
        if any(token in name for token in ("预算", "余额", "资产", "发票")):
            continue
        candidates.append(
            {
                "amount": float(amount),
                "category": "餐饮",
                "date": None,
                "description": name,
                "bill_type": "expense",
            }
        )
    return candidates


def _extract_budget_payload(goal: str) -> dict | None:
    """
    从 budget 任务的 goal 文本里，用正则抠出金额和周期，
    生成预算预览参数（用于确认卡预览，不落库）。
    """
    if "预算" not in (goal or ""):
        return None
    amount_match = re.search(r"(\d+(?:\.\d+)?)元", goal or "") or re.search(r"(\d+(?:\.\d+)?)", goal or "")
    period_match = re.search(r"(20\d{2}-\d{2}|20\d{2})", goal or "")
    if not amount_match:
        return None
    period = period_match.group(1) if period_match else ""
    return {
        "amount": float(amount_match.group(1)),
        "budget_type": "year" if len(period) == 4 else "month",
        "period": period,
        "category": "总预算",
        "is_total": True,
    }


def _build_plan_confirmation(ordered) -> dict | None:
    """
    基于 WorkflowPlan 的 task.goal 静态解析，生成"计划级确认卡"预览数据。
    不执行任何写操作，只把 bill 的账单候选和 budget 的预览参数拼进 confirmations。
    确认卡里的数据来自"计划文本解析"，不是"真实执行结果"。
    """
    confirmations = []
    for task in ordered:
        if task.type == "bill":
            candidates = _extract_bill_candidates(task.goal)
            if candidates:
                confirmations.append(
                    {
                        "need_confirm": True,
                        "entity": "bill",
                        "action": "batch_create",
                        "candidates": candidates,
                        "task_id": task.id,
                    }
                )
        elif task.type == "budget":
            payload = _extract_budget_payload(task.goal)
            if payload:
                confirmations.append(
                    {
                        "need_confirm": True,
                        "entity": "budget",
                        "action": "update",
                        "payload": payload,
                        "task_id": task.id,
                    }
                )
    if not confirmations:
        return None
    return {
        "need_confirm": True,
        "confirmations": confirmations,
    }


# ============================================================
# 跨域计划执行：按依赖顺序跑多个 Workflow
# ============================================================

def execute_plan(state: AgentState, plan: WorkflowPlan) -> AgentState:
    """
    跨 Workflow 计划执行：
    阶段 1（预览）：
      - 多任务且包含写操作 → 先返回"计划级确认卡"，不执行任何写操作
      - 确认卡附带 plan_tasks，供用户确认回传时重建计划
    阶段 2（执行，confirmed_plan=True）：
      - 拓扑排序后依序执行每个 Workflow
      - 前序任务结果截断后注入下一任务输入
      - 合并所有 output 和 intermediate_steps 返回
    """
    ordered = topo_sort(plan)
    if not ordered:
        return execute(state)

    state["workflow_plan"] = [t.model_dump() for t in ordered]

    # 预览模式：多任务 + 含可确认写操作 + 尚未经用户确认 → 先出确认卡
    if (
        len(ordered) > 1
        and any(task.type in _CONFIRM_TASKS for task in ordered)
        and not ((state.get("confirm") or {}).get("confirmed_plan"))
    ):
        confirm = _build_plan_confirmation(ordered)
        if confirm is not None:
            state["tool_results"] = []
            state["final_response"] = {
                "output": "请确认以下操作：",
                "confirm": confirm,
                "plan_tasks": state["workflow_plan"],
                "intermediate_steps": [],
            }
            return state

    multi = len(ordered) > 1
    user_input = state.get("user_input") or ""
    history = state.get("memory_messages") or []

    results: dict = {}
    outputs: list[str] = []
    steps: list = []
    for task in ordered:
        runner = _RUNNERS.get(task.type, bill.run)
        result = runner(_task_input(task, results, multi, user_input), state.get("user"), history=history)
        results[task.id] = result

        out = (result.get("output") or "").strip()
        if out:
            outputs.append(out)
        steps.extend(result.get("intermediate_steps") or [])

    state["workflow_results"] = results
    state["tool_results"] = steps
    state["final_response"] = {
        "output": "\n\n".join(outputs),
        "intermediate_steps": steps,
    }
    return state
