"""执行层：按 task_type 调用对应业务 Agent.run，写回统一结果。

各业务 Agent 自有管道；executor 只做调度与 state 回写，不假定具体构图。
结果形状 {output, intermediate_steps[, confirm]}，供 to_api_dict / SSE 复用。
"""

from __future__ import annotations

from account.ai.agents.crew.finance_planner import run_finance_planner
from account.ai.agents.supervisor import analysis, bill, budget

from .state import AgentState

_RUNNERS = {
    "bill": bill.run,
    "analysis": analysis.run,
    "budget": budget.run,
}


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
    if task == "bill" and state.get("confirm") is not None:
        kwargs["confirm"] = state.get("confirm")
    result = runner(state.get("user_input") or "", state.get("user"), **kwargs)
    state["tool_results"] = result.get("intermediate_steps") or []
    state["final_response"] = result
    return state
