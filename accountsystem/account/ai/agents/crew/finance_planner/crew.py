"""组装并运行 Finance Planner Crew，产出归一化结果交回 orchestrator。

对外唯一入口：run_finance_planner(user_input, user, history) -> dict
返回 {"output": str, "intermediate_steps": list, "crew_result": dict}，
结构对齐现有 to_api_dict（无 create_bill / 无 confirm 时回落为纯文本回复）。

执行链：Task Planner 选角色 -> 动态建 Task -> Crew 顺序执行 -> CrewResult。
"""

from __future__ import annotations

from account.ai.llm.llm_utils import log_agent_exc

from .schemas import CrewResult

_FALLBACK_REPLY = "暂时无法生成规划，可以尝试查询消费或预算"


def _history_to_text(history) -> str:
    """把 memory_messages 压成简短文本，供各角色参考上下文。"""
    if not history:
        return ""
    lines = []
    for m in history[-6:]:
        content = getattr(m, "content", None)
        if content is None and isinstance(m, dict):
            content = m.get("content")
        if content:
            lines.append(str(content))
    return "\n".join(lines)


def _extract_crew_result(crew_output) -> CrewResult:
    """从 CrewOutput 取出结构化结果；拿不到就用原始文本兜底。"""
    pydantic = getattr(crew_output, "pydantic", None)
    if isinstance(pydantic, CrewResult):
        return pydantic
    raw = getattr(crew_output, "raw", None) or str(crew_output or "")
    return CrewResult(summary=raw.strip()[:500], confidence=0.3)


def _format_report(result: CrewResult) -> str:
    """把结构化结果渲染成用户可读的纯文本报告（不使用 markdown）。"""
    parts = []
    if result.summary:
        parts.append(result.summary.strip())
    if result.analysis:
        parts.append("消费分析：")
        parts.extend(f"· {a}" for a in result.analysis)
    if result.suggestions:
        parts.append("规划建议：")
        parts.extend(f"· {s}" for s in result.suggestions)
    text = "\n".join(p for p in parts if p).strip()
    return text or _FALLBACK_REPLY


def _steps(specs) -> list[dict]:
    """Crew 执行轨迹，供未来 SSE 展示参与过的角色。"""
    return [{"agent": spec.role, "status": "completed"} for spec in specs]


def run_finance_planner(user_input: str, user=None, history=None) -> dict:
    """运行开放式财务规划 Crew。任何异常/依赖缺失都优雅降级，绝不抛出。"""
    try:
        from crewai import Crew, Process

        from .agents import build_agents
        from .planner import plan_tasks
        from .tasks import build_tasks

        history_text = _history_to_text(history)
        specs = plan_tasks(user_input, history_text)
        agents = build_agents([s.role for s in specs], user)
        tasks = build_tasks(specs, agents, user_input, history_text)

        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=False,
        )
        crew_output = crew.kickoff()
        result = _extract_crew_result(crew_output)
        return {
            "output": _format_report(result),
            "intermediate_steps": _steps(specs),
            "crew_result": result.model_dump(),
        }
    except Exception as e:
        log_agent_exc("CREW", e, input=(user_input or "")[:60])
        return {"output": _FALLBACK_REPLY, "intermediate_steps": []}
