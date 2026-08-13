"""构建 Finance Planner 的三个 CrewAI 角色。

关键约束：Crew Agent 不直接访问 ORM，只通过复用现有 LangChain Tool ->
Service -> DB。这里用一个适配器把 LangChain StructuredTool 包装成 CrewAI 工具，
并把鉴权后的 Django user 通过闭包注入（Agent 层不感知 user）。

crewai 全部在函数内部惰性导入，缺失时由 crew.py 统一降级。
"""

from __future__ import annotations

from account.ai.tools.finance_tools import (
    budget_advice_tool,
    build_analysis_tools,
    query_budget_tool,
)
from account.ai.knowledge.tools.knowledge_tools import build_knowledge_tools

from . import prompts


def _build_crew_llm():
    """用与项目一致的自建 OpenAI 兼容端点构建 CrewAI LLM（litellm）。"""
    from crewai import LLM

    from account.ai.llm.llm import (
        LLM_AGENT_API_KEY,
        LLM_AGENT_BASE_URL,
        LLM_AGENT_MODEL,
    )

    return LLM(
        model=f"openai/{LLM_AGENT_MODEL}",
        base_url=LLM_AGENT_BASE_URL,
        api_key=LLM_AGENT_API_KEY,
        temperature=0.2,
    )


def _wrap_tool(lc_tool):
    """把一个 LangChain StructuredTool 适配为 CrewAI BaseTool。

    参数 schema 直接复用 LangChain 侧的 args_schema，_run 转调原 Tool.invoke，
    从而保持 Crew Agent -> LangChain Tool -> Service -> DB 的调用链。
    """
    from crewai.tools import BaseTool as CrewBaseTool

    class _Adapter(CrewBaseTool):
        name: str = lc_tool.name
        description: str = lc_tool.description
        args_schema: type = lc_tool.args_schema

        def _run(self, **kwargs) -> str:
            return lc_tool.invoke(kwargs)

    return _Adapter()


def _planner_tools(user):
    """预算规划师：只读预算工具，避免开放报告过程中产生未确认的写库副作用。"""
    return [query_budget_tool(user), budget_advice_tool(user)]


def build_finance_planner_agents(user):
    """返回 (analyst, planner, advisor) 三个已注入工具与 LLM 的 CrewAI Agent。"""
    from crewai import Agent

    crew_llm = _build_crew_llm()

    analyst = Agent(
        role=prompts.ANALYST_ROLE,
        goal=prompts.ANALYST_GOAL,
        backstory=prompts.ANALYST_BACKSTORY,
        tools=[_wrap_tool(t) for t in build_analysis_tools(user)],
        llm=crew_llm,
        allow_delegation=False,
        verbose=False,
    )
    planner = Agent(
        role=prompts.PLANNER_ROLE,
        goal=prompts.PLANNER_GOAL,
        backstory=prompts.PLANNER_BACKSTORY,
        tools=[_wrap_tool(t) for t in _planner_tools(user)],
        llm=crew_llm,
        allow_delegation=False,
        verbose=False,
    )
    advisor = Agent(
        role=prompts.ADVISOR_ROLE,
        goal=prompts.ADVISOR_GOAL,
        backstory=prompts.ADVISOR_BACKSTORY,
        tools=[_wrap_tool(t) for t in build_knowledge_tools()],
        llm=crew_llm,
        allow_delegation=False,
        verbose=False,
    )
    return analyst, planner, advisor
