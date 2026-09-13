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

import logging

from account.ai.agents.crew.finance_planner import run_finance_planner
from account.ai.agents.supervisor import asset, bill, budget, chat, invoice

from .events import EventEmitter
from .protocol import StepStatus
from .result_adapter import adapt_workflow_result
from .result_aggregator import aggregate_plan_results
from .response_composer import compose_response
from .state import AgentState
from .task_schema import WorkflowPlan, topo_sort

logger = logging.getLogger(__name__)


# ============================================================
# 常量：业务映射与执行参数
# ============================================================

# task_type → 对应业务 Agent.run 的映射表
_RUNNERS = {
    "bill": bill.run,
    "budget": budget.run,
    "asset": asset.run,
    "invoice": invoice.run,
    "chat": chat.run,
}

# 带 human_confirm 机制、能接收确认卡片回传的业务域
_CONFIRM_TASKS = frozenset({"bill", "budget", "asset", "invoice"})
_WRITE_ACTIONS = {
    "bill": frozenset({"create", "batch_create", "update", "delete"}),
    "budget": frozenset({"set_budget"}),
    "asset": frozenset({"create", "update", "delete", "adjust_balance"}),
    "invoice": frozenset({"create", "update", "delete"}),
}
_CONFIRM_ACTIONS = {
    "bill": frozenset({"create", "batch_create", "update", "delete"}),
    "budget": frozenset({"set_budget"}),
    "asset": frozenset({"create", "update", "delete", "adjust_balance"}),
    "invoice": frozenset({"update", "delete"}),
}

# 定向写操作：确认前必须先由 Workflow 定位唯一目标（0/1/N）。
_TARGETED_ACTIONS = {
    "bill": frozenset({"update", "delete"}),
    "asset": frozenset({"update", "delete", "adjust_balance"}),
    "invoice": frozenset({"update", "delete"}),
}
# 各域输入里承载显式目标 id 的字段
_TARGET_ID_FIELDS = {"bill": "bill_id", "asset": "account_id", "invoice": "invoice_id"}

# 前序任务结果注入下一任务时的最大字符数，防止 prompt 无限膨胀
_PREV_RESULT_MAX_CHARS = 800

_AGENT_NAMES = {
    "bill": "bill",
    "budget": "budget",
    "asset": "asset",
    "invoice": "invoice",
    "chat": "chat",
    "open_planning": "finance_planner",
}

# task.type + task.action → 面向用户的执行状态文案。
# 前端 executionStatus 直接消费事件 message，不再自行根据 type/action 猜测。
_TASK_STATUS_TEXT = {
    ("bill", "query"): "正在查询账单…",
    ("bill", "create"): "正在整理账单信息…",
    ("bill", "batch_create"): "正在整理账单信息…",
    ("bill", "update"): "正在检查账单修改…",
    ("bill", "delete"): "正在检查账单删除…",
    ("budget", "set_budget"): "正在调整预算…",
    ("budget", "query_budget"): "正在查询预算…",
    ("budget", "budget_advice"): "正在分析预算建议…",
    ("asset", "create"): "正在创建资产…",
    ("asset", "query"): "正在查询资产…",
    ("asset", "update"): "正在检查资产修改…",
    ("asset", "delete"): "正在检查资产删除…",
    ("asset", "adjust_balance"): "正在调整资产余额…",
    ("invoice", "create"): "正在整理发票信息…",
    ("invoice", "query"): "正在查询发票…",
    ("invoice", "update"): "正在检查发票修改…",
    ("invoice", "delete"): "正在检查发票删除…",
    ("open_planning", "analyze"): "正在分析你的财务情况…",
    ("chat", "respond"): "正在思考…",
}


def _status_text(task_type: str, task_action: str) -> str:
    return _TASK_STATUS_TEXT.get((task_type, task_action), "正在处理…")


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
# 跨计划辅助函数：上下文拼装 + 预览数据提取
# ============================================================

def _task_input(task, results: dict, user_input: str) -> str:
    """组装任务目标和前序结果上下文，不改变结构化执行参数。"""
    text = (task.goal or "").strip() or user_input
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

# ============================================================
# 单任务执行：交给某个业务 Agent 跑一次
# ============================================================

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
    runner = _RUNNERS.get(task_type)
    if runner is None:
        raise ValueError(f"no runner registered for task type {task_type!r}")
    kwargs = {
        "history": state.get("memory_messages") or [],
        "task_action": task.action,
        "task_input": task.input_model.model_dump(mode="json"),
        "task_confirmed": bool((state.get("confirm") or {}).get("confirmed_plan")),
    }
    confirm = state.get("confirm")
    if task_type in _CONFIRM_TASKS and confirm is not None:
        kwargs["confirm"] = confirm
    return runner(user_input, state.get("user"), **kwargs)


def _build_plan_confirmation(ordered) -> dict | None:
    """Build confirmation data from validated task actions and inputs."""
    confirmations = []
    for task in ordered:
        if task.action not in _CONFIRM_ACTIONS.get(task.type, ()):
            continue
        payload = task.input_model.model_dump(mode="json")
        item = {
            "need_confirm": True,
            "entity": task.type,
            "action": task.action,
            "payload": payload,
            "task_id": task.id,
        }
        if task.type == "bill" and task.action == "batch_create":
            item["candidates"] = payload["items"]
        confirmations.append(item)
    if not confirmations:
        return None
    return {"need_confirm": True, "confirmations": confirmations}


def _has_confirm_action(ordered) -> bool:
    return any(task.action in _CONFIRM_ACTIONS.get(task.type, ()) for task in ordered)


def _needs_target_resolution(task) -> bool:
    """定向写操作但输入没有显式目标 id → 目标待定位，不能提前出计划级确认卡。"""
    if task.action not in _TARGETED_ACTIONS.get(task.type, ()):
        return False
    field = _TARGET_ID_FIELDS[task.type]
    value = (task.input_model.model_dump(mode="json") or {}).get(field)
    return not isinstance(value, int)


def _has_previewable_action(ordered) -> bool:
    """计划里存在"无需定位即确认"的写操作（create/batch/set_budget 或带显式 id 的定向写）。

    仅当全是"目标待定位"的 update/delete 时才不预览，交给 Workflow 先定位再确认。
    """
    return any(
        task.action in _CONFIRM_ACTIONS.get(task.type, ())
        and not _needs_target_resolution(task)
        for task in ordered
    )


def _dump_plan_tasks(tasks) -> list[dict]:
    """WorkflowTask 列表 → 可回灌 WorkflowPlan 的纯 dict（含显式 input）。"""
    dumped = []
    for task in tasks:
        item = task.model_dump()
        item["input"] = task.input_model.model_dump(mode="json")
        dumped.append(item)
    return dumped


def _remaining_plan_tasks(ordered, start_index: int) -> list[dict]:
    """暂停点起的剩余任务；depends_on 只保留仍在剩余集合内的依赖，保证可单独回放。"""
    remaining = _dump_plan_tasks(ordered[start_index:])
    ids = {item["id"] for item in remaining}
    for item in remaining:
        item["depends_on"] = [dep for dep in (item.get("depends_on") or []) if dep in ids]
    return remaining


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
      - 计划里存在"无需定位即确认"的写操作时，返回"计划级确认卡"，不执行任何写操作
      - 全是"目标待定位"的 update/delete 时不预览：交给 Workflow 先定位(0/1/N)再出确认卡
      - 确认卡附带服务端保存的 workflow_plan，plan_tasks 仅用于展示兼容
    阶段 2（执行，confirmed_plan=True）：
      - 拓扑排序后依序执行每个 Workflow；中途再次暂停（确认/缺参数）只回放剩余任务
      - 前序任务结果截断后注入下一任务输入
      - 合并所有 output 和 intermediate_steps 返回
    """
    ordered = topo_sort(plan)
    if not ordered:
        state["tool_results"] = []
        state["final_response"] = {
            "output": "计划依赖无效，未执行任何操作。",
            "plan_result": {
                "plan_id": str(state.get("conversation_id") or runtime_plan_id or "plan"),
                "status": "failed",
                "task_results": [],
                "summary": "计划依赖校验失败",
                "analysis_view": {},
                "intermediate_steps": [],
            },
            "intermediate_steps": [],
        }
        return state

    state["workflow_plan"] = [t.model_dump() if hasattr(t, "model_dump") else {
        "id": t.id, "type": t.type, "goal": t.goal, "depends_on": t.depends_on
    } for t in ordered]

    plan_id = str(state.get("conversation_id") or runtime_plan_id or "plan")

    if (
        _has_previewable_action(ordered)
        and _has_confirm_action(ordered)
        and not ((state.get("confirm") or {}).get("confirmed_plan"))
    ):
        try:
            confirm = _build_plan_confirmation(ordered)
        except (KeyError, TypeError, ValueError):
            confirm = None
        if confirm is None:
            state["tool_results"] = []
            state["final_response"] = {
                "output": "无法构造安全的确认信息，计划未执行。",
                "plan_result": {
                    "plan_id": plan_id,
                    "status": "failed",
                    "task_results": [],
                    "summary": "确认信息构造失败，计划未执行",
                    "analysis_view": {},
                    "intermediate_steps": [],
                },
                "intermediate_steps": [],
            }
            return state
        state["tool_results"] = []
        state["final_response"] = {
            "output": "请确认以下操作：",
            "confirm": confirm,
            # plan_tasks is a presentation-compatible copy; workflow_plan is authoritative.
            "plan_tasks": state["workflow_plan"],
            "workflow_plan": state["workflow_plan"],
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
        message="正在处理你的请求…",
    )

    user_input = state.get("user_input") or ""
    history = state.get("memory_messages") or []

    results: dict = {}
    outputs: list[str] = []
    steps: list = []
    task_results = []
    had_failure = False
    for index, task in enumerate(ordered):
        agent_name = _AGENT_NAMES[task.type]
        _emit(
            event_emitter,
            "task.started",
            trace_id=trace_id,
            plan_id=plan_id,
            task_id=task.id,
            agent=agent_name,
            message=_status_text(task.type, task.action),
        )
        _emit(
            event_emitter,
            "agent.started",
            trace_id=trace_id,
            plan_id=plan_id,
            task_id=task.id,
            agent=agent_name,
            message=_status_text(task.type, task.action),
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
            # 单个 Workflow 崩溃不拖垮整条计划：完整 traceback 落服务端日志，
            # 该步转成 FAILED 结果，保留已完成 Task，SSE 正常收尾（不向上抛）
            had_failure = True
            logger.exception("plan task failed: plan=%s task=%s", plan_id, task.id)
            _emit(
                event_emitter,
                "agent.failed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message="处理失败，请稍后再试",
            )
            _emit(
                event_emitter,
                "task.failed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message="处理失败，请稍后再试",
            )
            task_results.append(
                adapt_workflow_result(
                    {
                        "success": False,
                        "message": "处理失败，请稍后再试",
                        "error": {"code": "workflow_exception", "message": "处理失败，请稍后再试"},
                    },
                    plan_id=plan_id,
                    step_id=task.id,
                    step_type=task.type,
                    action=task.action,
                )
            )
            break

        results[task.id] = result
        step_result = adapt_workflow_result(
            result,
            plan_id=plan_id,
            step_id=task.id,
            step_type=task.type,
            action=task.action,
        )
        task_results.append(step_result)

        out = (result.get("output") or "").strip()
        if out:
            outputs.append(out)
        steps.extend(result.get("intermediate_steps") or [])

        if step_result.status == StepStatus.WAITING_CONFIRMATION:
            # 目标已由 Workflow 定位，但用户还没确认：交回确认卡并暂停。
            # 只持久化剩余任务，确认后不会重跑已执行过的部分
            raw = result.get("confirm") or {}
            payload = raw.get("payload") or result.get("data") or {}
            item = {
                "need_confirm": True,
                "entity": raw.get("entity") or str(step_result.step_type),
                "action": raw.get("action") or step_result.action,
                "payload": payload if isinstance(payload, dict) else {},
                "candidates": raw.get("candidates") or [],
                "task_id": step_result.step_id,
            }
            remaining = _remaining_plan_tasks(ordered, index)
            state["workflow_results"] = results
            state["tool_results"] = steps
            state["final_response"] = {
                "output": out or "请确认以下操作：",
                "confirm": {"need_confirm": True, "confirmations": [item]},
                # plan_tasks 供落库兼容；workflow_plan 为权威回放副本
                "plan_tasks": remaining,
                "workflow_plan": remaining,
                "trace_id": trace_id,
                "plan_id": plan_id,
                "intermediate_steps": steps,
            }
            return state

        if step_result.status == StepStatus.WAITING_INPUT:
            # 缺参数/目标：停下询问用户，不是失败；收尾交给聚合 + Composer 出询问文案
            _emit(
                event_emitter,
                "agent.completed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
            )
            _emit(
                event_emitter,
                "task.completed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
            )
            break

        if step_result.success:
            # 完成事件不携带"正在…"文案：前端保留上一状态，等下一个 task.started 或 done 清空
            _emit(
                event_emitter,
                "agent.completed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
            )
            _emit(
                event_emitter,
                "task.completed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
            )
        else:
            had_failure = True
            _emit(
                event_emitter,
                "agent.failed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message="处理失败，请稍后再试",
            )
            _emit(
                event_emitter,
                "task.failed",
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task.id,
                agent=agent_name,
                message="处理失败，请稍后再试",
            )
            break

    state["workflow_results"] = results
    state["tool_results"] = steps
    plan_result = aggregate_plan_results(
        task_results,
        plan_id=plan_id,
    )
    reply = compose_response(plan_result)
    if reply:
        plan_result.summary = reply
    state["plan_result"] = plan_result
    state["final_response"] = {
        "output": reply or plan_result.summary or "本次计划已处理",
        "plan_result": plan_result.model_dump(mode="json"),
        "intermediate_steps": steps,
    }
    if had_failure or plan_result.status == "failed":
        _emit(
            event_emitter,
            "plan.failed",
            trace_id=trace_id,
            plan_id=plan_id,
            message="处理失败，请稍后再试",
        )
    elif plan_result.status == "success":
        _emit(
            event_emitter,
            "plan.completed",
            trace_id=trace_id,
            plan_id=plan_id,
            message="处理完成",
        )
    # partial 且无失败（例如等用户补参数）：不播报终态，交给 done 清空
    return state
