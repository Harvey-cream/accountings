"""
Executor 执行层模块
================================================================
作用：根据统一 WorkflowPlan，按依赖顺序调用具体业务 Agent，并把结果
      统一写回 state.final_response。

execute_plan 是唯一正式执行入口，覆盖单任务、多任务和确认恢复场景。
输出形状统一为 {output, intermediate_steps[, confirm][, plan_tasks]}，
供 to_api_dict / SSE / 消息落库复用。
================================================================
"""

from __future__ import annotations

from account.ai.agents.crew.finance_planner import run_finance_planner
from account.ai.agents.supervisor import asset, bill, budget, invoice

from .events import EventEmitter
from .result_adapter import adapt_workflow_result
from .result_aggregator import aggregate_plan_results
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
_CONFIRM_TASKS = frozenset({"bill", "budget", "asset", "invoice"})

# 前序任务结果注入下一任务时的最大字符数，防止 prompt 无限膨胀
_PREV_RESULT_MAX_CHARS = 800

_AGENT_NAMES = {
    "bill": "bill",
    "budget": "budget",
    "asset": "asset",
    "invoice": "invoice",
    "open_planning": "finance_planner",
}


def _emit(emitter, event_type, *, trace_id, plan_id, task_id="", agent="", message=""):
    if emitter is not None:
        emitter.emit(
            event_type,
            trace_id=trace_id,
            plan_id=plan_id,
            task_id=task_id,
            agent=agent,
            message=message,
        )


# ============================================================
# 单任务执行：交给某个业务 Agent 跑一次
# ============================================================

def _task_input(task, results: dict, user_input: str) -> str:
    """组装任务输入：优先使用自包含 goal，再补充依赖任务摘要。"""
    text = (getattr(task, "goal", "") or "").strip() or user_input
    prev = [
        (results[dep].get("output") or "").strip()
        for dep in getattr(task, "depends_on", [])
        if dep in results
    ]
    prev = [p for p in prev if p]
    if prev:
        joined = "\n\n".join(p[:_PREV_RESULT_MAX_CHARS] for p in prev)
        text = f"{text}\n\n参考前序任务结果：\n{joined}"
    return text


def _execute_task(
    state: AgentState,
    task,
    results: dict,
    *,
    trace_id: str = "",
    plan_id: str = "",
    event_emitter: EventEmitter | None = None,
) -> dict:
    task_type = task.type
    user_input = _task_input(task, results, state.get("user_input") or "")
    if task_type == "open_planning":
        return run_finance_planner(
            user_input,
            state.get("user"),
            history=state.get("memory_messages") or [],
            trace_id=trace_id,
            plan_id=plan_id,
            task_id=task.id,
            event_emitter=event_emitter,
        )
    runner = _RUNNERS.get(task_type, bill.run)
    kwargs = {"history": state.get("memory_messages") or []}
    confirm = state.get("confirm")
    if task_type in _CONFIRM_TASKS and confirm is not None:
        kwargs["confirm"] = confirm
    if task_type in {"asset", "invoice"}:
        task_input = getattr(task, "input", {}) or {}
        kwargs["task_input"] = task_input
    return runner(user_input, state.get("user"), **kwargs)

# ============================================================
# 跨计划辅助函数：上下文拼装 + 预览数据提取
# ============================================================

def _task_input(task, results: dict, user_input: str) -> str:
    """
    组装某个子任务的输入文本：
      - 多任务场景：用 task.goal（自包含目标），避免其他域的诉求干扰
      - 单任务场景：直接用原始 user_input，避免 goal 里丢失细节
      - 有依赖时，把前序任务的 output 截断后附加进去，作为上下文
    """
    text = (task.goal or "").strip() or user_input
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


def _build_plan_confirmation(ordered) -> dict | None:
    """Build confirmation data directly from structured Task.input."""
    confirmations = []
    for task in ordered:
        task_input = task.input or {}
        if task.type == "bill":
            items = task_input.get("items") or []
            if items:
                confirmations.append({
                    "need_confirm": True,
                    "entity": "bill",
                    "action": "batch_create",
                    "candidates": items,
                    "task_id": task.id,
                })
        elif task.type == "budget" and task_input:
            confirmations.append({
                "need_confirm": True,
                "entity": "budget",
                "action": "update",
                "payload": task_input,
                "task_id": task.id,
            })
        elif task.type in {"asset", "invoice"}:
            action = str(task_input.get("action") or "").strip()
            if action in {"create", "update", "delete", "adjust_balance"} and (
                task.type == "asset" or action in {"update", "delete"}
            ):
                confirmations.append({
                    "need_confirm": True,
                    "entity": task.type,
                    "action": action,
                    "candidates": task_input.get("candidates") or [],
                    "payload": task_input,
                    "task_id": task.id,
                })
    if not confirmations:
        return None
    return {"need_confirm": True, "confirmations": confirmations}


# ============================================================
# 跨域计划执行：按依赖顺序跑多个 Workflow
# ============================================================

def execute_plan(
    state: AgentState,
    plan: WorkflowPlan,
    *,
    trace_id: str = "",
    runtime_plan_id: str = "",
    event_emitter: EventEmitter | None = None,
) -> AgentState:
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
        return state

    state["workflow_plan"] = [t.model_dump() if hasattr(t, "model_dump") else {
        "id": t.id, "type": t.type, "goal": t.goal, "depends_on": t.depends_on
    } for t in ordered]

    plan_id = str(state.get("conversation_id") or runtime_plan_id or "plan")

    # 预览模式：计划包含可确认写操作且尚未经用户确认时，统一返回计划级确认卡
    if (
        any(task.type in _CONFIRM_TASKS for task in ordered)
        and not ((state.get("confirm") or {}).get("confirmed_plan"))
    ):
        confirm = _build_plan_confirmation(ordered)
        if confirm is not None:
            state["tool_results"] = []
            state["final_response"] = {
                "output": "请确认以下操作：",
                "confirm": confirm,
                "plan_tasks": state["workflow_plan"],
                "trace_id": trace_id,
                "plan_id": plan_id,
                "intermediate_steps": [],
            }
            return state

    _emit(
        event_emitter,
        "plan.started",
        trace_id=trace_id,
        plan_id=plan_id,
        message="开始执行计划",
    )

    user_input = state.get("user_input") or ""
    history = state.get("memory_messages") or []

    results: dict = {}
    outputs: list[str] = []
    steps: list = []
    task_results = []
    for task in ordered:
        agent_name = _AGENT_NAMES[task.type]
        _emit(
            event_emitter,
            "task.started",
            trace_id=trace_id,
            plan_id=plan_id,
            task_id=task.id,
            agent=agent_name,
            message=f"开始处理{task.type}",
        )
        _emit(
            event_emitter,
            "agent.started",
            trace_id=trace_id,
            plan_id=plan_id,
            task_id=task.id,
            agent=agent_name,
            message=f"{agent_name} 开始执行",
        )
        try:
            result = _execute_task(
                state,
                task,
                results,
                trace_id=trace_id,
                plan_id=plan_id,
                event_emitter=event_emitter,
            )
        except Exception:
            _emit(
                event_emitter,
                "agent.failed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message=f"{agent_name} 执行失败",
            )
            _emit(
                event_emitter,
                "task.failed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message=f"{task.type} 处理失败",
            )
            _emit(
                event_emitter,
                "plan.failed",
                trace_id=trace_id,
                plan_id=plan_id,
                message="计划执行失败",
            )
            raise

        results[task.id] = result
        step_result = adapt_workflow_result(
            result,
            plan_id=plan_id,
            step_id=task.id,
            step_type=task.type,
        )
        task_results.append(step_result)

        out = (result.get("output") or "").strip()
        if out:
            outputs.append(out)
        steps.extend(result.get("intermediate_steps") or [])
        if step_result.success:
            _emit(
                event_emitter,
                "agent.completed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message=f"{agent_name} 执行完成",
            )
            _emit(
                event_emitter,
                "task.completed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message=f"{task.type} 处理完成",
            )
        else:
            _emit(
                event_emitter,
                "agent.failed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message=f"{agent_name} 执行失败",
            )
            _emit(
                event_emitter,
                "task.failed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message=f"{task.type} 处理失败",
            )
            break

    state["workflow_results"] = results
    state["tool_results"] = steps
    plan_result = aggregate_plan_results(
        task_results,
        plan_id=plan_id,
    )
    state["plan_result"] = plan_result
    state["final_response"] = {
        "output": plan_result.summary or "本次计划已处理",
        "plan_result": plan_result.model_dump(mode="json"),
        "intermediate_steps": steps,
    }
    if plan_result.status == "success":
        _emit(
            event_emitter,
            "plan.completed",
            trace_id=trace_id,
            plan_id=plan_id,
            message="计划执行完成",
        )
    else:
        _emit(
            event_emitter,
            "plan.failed",
            trace_id=trace_id,
            plan_id=plan_id,
            message="计划执行失败",
        )
    return state
