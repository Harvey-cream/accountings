"""执行层：按 task_type 调用对应业务 Agent.run，写回统一结果。

各业务 Agent 自有管道；executor 只做调度与 state 回写，不假定具体构图。
结果形状 {output, intermediate_steps[, confirm]}，供 to_api_dict / SSE 复用。

execute       —— 单任务：bill / budget / asset / invoice / open_planning(CrewAI)
execute_plan  —— Task Planner 产出的跨 Workflow 计划：按依赖序执行多个域
"""

from __future__ import annotations

from account.ai.agents.crew.finance_planner import run_finance_planner
from account.ai.agents.supervisor import asset, bill, budget, invoice

from .state import AgentState
from .task_schema import WorkflowPlan, topo_sort

_RUNNERS = {
    "bill": bill.run,
    "budget": budget.run,
    "asset": asset.run,
    "invoice": invoice.run,
}

# 带 human_confirm 机制、能接收确认卡片回传的业务域
_CONFIRM_TASKS = frozenset({"bill", "asset", "invoice"})

# 依赖结果注入下一任务时的最大长度，防止 prompt 无限膨胀
_PREV_RESULT_MAX_CHARS = 800


def execute(state: AgentState) -> AgentState:
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


def _task_input(task, results: dict, multi: bool, user_input: str) -> str:
    """组装某个子任务的输入：goal 自包含 + 截断后的前序依赖结果。

    单任务计划直接用原始输入（goal 可能丢失细节，如金额）；
    多任务计划用 goal，避免其他域的诉求干扰当前 Workflow。
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


def execute_plan(state: AgentState, plan: WorkflowPlan) -> AgentState:
    """按依赖序执行跨 Workflow 计划，逐步共享结果，合并统一输出。

    计划无法排序（理论上已被 task_planner 校验拦截）时回落单任务 execute。
    某一步要求人工确认（bill/asset/invoice 写操作）时立即中断，把确认卡片交回前端。
    """
    ordered = topo_sort(plan)
    if not ordered:
        return execute(state)

    state["workflow_plan"] = [t.model_dump() for t in ordered]
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

        # 写操作需人工确认：中断计划，确认卡片交回前端（不绕过 human_confirm）
        if (result.get("confirm") or {}).get("need_confirm"):
            state["workflow_results"] = results
            state["tool_results"] = result.get("intermediate_steps") or []
            state["final_response"] = result
            return state

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
