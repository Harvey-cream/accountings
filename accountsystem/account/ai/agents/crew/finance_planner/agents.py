"""Finance Planner 的角色池：按需构建 CrewAI Agent。

关键约束：
1. Crew Agent 不直接访问 ORM，只通过复用现有 LangChain Tool -> Service -> DB；
2. Crew 只允许只读工具，写操作（记账/改账单/建预算）必须走 LangGraph Workflow；
3. financial_advisor 不持有任何业务工具，只做汇总。

crewai 全部在函数内部惰性导入，缺失时由 crew.py 统一降级。
"""

from __future__ import annotations

from account.ai.knowledge.tools.knowledge_tools import build_knowledge_tools
from account.ai.llm.llm import AGENT_MAX_ITERATIONS
from account.ai.tools.finance_tools import (
    budget_advice_tool,
    build_analysis_tools,
    query_asset_structure_tool,
    query_asset_summary_tool,
    query_budget_tool,
)

from . import prompts

# Crew 可用工具白名单：任何不在此列的（尤其是写操作）都会被过滤掉
_READONLY_TOOLS = frozenset(
    {
        "analyze_expense",
        "compare_periods",
        "query_asset_summary",
        "query_asset_structure",
        "query_budget",
        "budget_advice",
        "search_finance_knowledge",
    }
)


def _build_crew_llm():
    """用与项目一致的自建 OpenAI 兼容端点构建 CrewAI LLM（litellm）。

    fallbacks 经 crewai 的 additional_params 透传给 litellm.completion，由其原生
    兜底机制在**每次**调用失败时顺延下一个模型（litellm 会把主模型的 api_base /
    api_key 一并带给兜底模型）。
    """
    from crewai import LLM

    from account.ai.llm.llm import (
        LLM_AGENT_API_KEY,
        LLM_AGENT_BASE_URL,
        LLM_AGENT_FALLBACK_MODELS,
        LLM_AGENT_MODEL,
    )

    return LLM(
        model=f"openai/{LLM_AGENT_MODEL}",
        base_url=LLM_AGENT_BASE_URL,
        api_key=LLM_AGENT_API_KEY,
        temperature=0.2,
        fallbacks=[
            f"openai/{name}"
            for name in LLM_AGENT_FALLBACK_MODELS
            if name != LLM_AGENT_MODEL
        ],
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


def _role_tools(role: str, user) -> list:
    """按角色取工具，并用白名单挡掉一切写操作。"""
    if role == "financial_analyst":
        tools = [
            *build_analysis_tools(user),
            query_asset_summary_tool(user),
            query_asset_structure_tool(user),
        ]
    elif role == "budget_planner":
        tools = [
            query_budget_tool(user),
            budget_advice_tool(user),
            query_asset_summary_tool(user),
        ]
    elif role == "knowledge_researcher":
        tools = build_knowledge_tools()
    else:  # financial_advisor 只做汇总，不持有业务工具
        return []
    return [t for t in tools if t.name in _READONLY_TOOLS]


def build_agents(roles, user) -> dict:
    """按需构建角色池中被选中的 Agent，返回 {role_key: Agent}（保持传入顺序）。"""
    from crewai import Agent

    crew_llm = _build_crew_llm()

    agents: dict = {}
    for role in roles:
        if role in agents:
            continue
        profile = prompts.ROLE_PROFILES[role]
        agents[role] = Agent(
            role=profile["role"],
            goal=profile["goal"],
            backstory=profile["backstory"],
            tools=[_wrap_tool(t) for t in _role_tools(role, user)],
            llm=crew_llm,
            allow_delegation=False,
            verbose=False,
            max_iter=AGENT_MAX_ITERATIONS,
        )
    return agents
