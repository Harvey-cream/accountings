import json
from dataclasses import dataclass
from typing import Callable

from langchain_core.tools import StructuredTool

from . import prompt
from .llm_utils import extract_content, json_from_text, log_agent_exc
from .schemas import (
    APP_HELP_EMPTY_REPLY,
    BILL_SUMMARY_EMPTY_REPLY,
    BILL_SUMMARY_NO_USER,
    DEFAULT_CHAT_REPLY,
    AccountingResult,
    TextReply,
)


@dataclass(frozen=True)
class ToolMeta:
    name: str
    description: str
    tags: tuple[str, ...]  # FC 失败时 fallback 关键词（仅中文 tag 参与匹配）
    routed: bool = True


_ROUTED_METAS: list[ToolMeta] = []


def agent_tool(name: str, description: str, tags: tuple[str, ...], *, routed: bool = True):
    def decorator(fn: Callable) -> Callable:
        meta = ToolMeta(name=name, description=description, tags=tags, routed=routed)
        fn.tool_meta = meta  # type: ignore[attr-defined]
        if routed:
            _ROUTED_METAS.append(meta)
        return fn

    return decorator


@dataclass(frozen=True)
class ToolRunContext:
    user: object
    llm: object
    retrieve_kb: Callable
    get_summary: Callable
    llm_model: str
    llm_base_url: str


def _dispatch(name: str, user_message: str, ctx: ToolRunContext) -> str:
    """按工具名调用对应 run_*，注入 llm / user 等运行时上下文。"""
    if name == "answer_app_help":
        return run_answer_app_help(
            user_message, ctx.llm, ctx.retrieve_kb, ctx.llm_model, ctx.llm_base_url
        )
    if name == "query_bill_summary":
        return run_query_bill_summary(
            user_message,
            ctx.user,
            ctx.llm,
            ctx.get_summary,
            ctx.llm_model,
            ctx.llm_base_url,
        )
    return run_record_transaction(user_message, ctx.llm, ctx.llm_model, ctx.llm_base_url)


def build_bindable_tools(ctx: ToolRunContext) -> list[StructuredTool]:
    """注册表 → LangChain StructuredTool，供 bind_tools 发给模型做 function calling。"""
    tools: list[StructuredTool] = []

    def _make_fn(tool_name: str):
        def _run(user_message: str) -> str:
            return _dispatch(tool_name, user_message, ctx)

        _run.__name__ = tool_name
        return _run

    for meta in _ROUTED_METAS:
        # StructuredTool (langchain 0.1.x) 只认 pydantic v1 schema，从函数签名推断即可。
        tools.append(
            StructuredTool.from_function(
                func=_make_fn(meta.name),
                name=meta.name,
                description=meta.description,
            )
        )
    return tools


def run_routed_tool(name: str, user_message: str, ctx: ToolRunContext) -> str:
    """解析 tool_calls 后执行工具；未知工具名回退 record_transaction。"""
    valid = {m.name for m in _ROUTED_METAS}
    if name not in valid:
        print(f"[FC] unknown tool {name!r}, fallback record_transaction")
        name = "record_transaction"
    return _dispatch(name, user_message, ctx)


def fallback_tool_name(user_input: str) -> str | None:
    """FC 失败时按 tags 猜工具名；无匹配返回 None（走闲聊）。"""
    text = user_input or ""
    for meta in _ROUTED_METAS:
        kws = (t for t in meta.tags if any("\u4e00" <= c <= "\u9fff" for c in t))
        if any(kw in text for kw in kws):
            return meta.name
    if any(ch.isdigit() for ch in text):
        return "record_transaction"
    return None


@agent_tool(
    name="answer_app_help",
    description=(
        "Answer product/how-to questions from the knowledge base. "
        "Returns a short Chinese explanation. "
        "Use when: how to use the app, features, categories, tutorials. "
        "Do NOT use when: querying the user's real bill numbers."
    ),
    tags=("help", "教程", "怎么", "如何", "功能", "分类", "用法"),
)
def run_answer_app_help(
    user_message: str, llm, retrieve_kb, llm_model: str, llm_base_url: str
) -> str:
    kb_context = retrieve_kb(user_message) or (
        "怎么手动记账：打开APP→点击底部‘记账’→选择收入或支出→填写金额、分类、备注→保存即可。"
    )
    print(f"[LLM] tool=answer_app_help model={llm_model}")
    raw = extract_content(llm.invoke(prompt.build_app_help_prompt(user_message, kb_context)))
    return TextReply(reply=raw or APP_HELP_EMPTY_REPLY).reply


@agent_tool(
    name="query_bill_summary",
    description=(
        "Query the current user's bill summary for the last 30 days. "
        "Returns a natural-language answer with real totals. "
        "Use when: how much spent/earned, monthly summary, category breakdown. "
        "Do NOT use when: logging a new transaction with an amount."
    ),
    tags=("query", "stats", "多少", "统计", "汇总", "一共", "共", "报表", "结余", "本月", "近30天"),
)
def run_query_bill_summary(
    user_message: str, user, llm, get_summary, llm_model: str, llm_base_url: str
) -> str:
    if user is None:
        return TextReply(reply=BILL_SUMMARY_NO_USER).reply
    print(f"[LLM] tool=query_bill_summary model={llm_model}")
    raw = extract_content(
        llm.invoke(prompt.build_bill_summary_prompt(user_message, get_summary(user)))
    )
    while "  " in raw:
        raw = raw.replace("  ", " ")
    return TextReply(reply=raw.strip() or BILL_SUMMARY_EMPTY_REPLY).reply


@agent_tool(
    name="record_transaction",
    description=(
        "Parse the user message into one new income/expense transaction. "
        "Returns type, category, money, account, remark, reply. "
        "Use when: specific amount or logging a purchase/income "
        "(e.g. 'coffee 18 yuan', 'salary arrived 5000'). "
        "Do NOT use when: asking totals like 'how much did I spend this month'."
    ),
    tags=("record", "记账", "花了", "买了", "到账", "工资"),
)
def run_record_transaction(user_message: str, llm, llm_model: str, llm_base_url: str) -> str:
    p = prompt.build_record_prompt(user_message)
    print(f"[LLM] tool=record_transaction model={llm_model} input={user_message[:40]!r}")
    try:
        structured = llm.with_structured_output(AccountingResult)
        result = structured.invoke(p)
        if isinstance(result, dict):
            result = AccountingResult.model_validate(result)
    except Exception as e:
        log_agent_exc("LLM", e, tool="record_transaction", stage="structured", input=user_message[:40])
        try:
            raw = extract_content(llm.invoke(p))
            result = AccountingResult.model_validate_json(json_from_text(raw))
        except Exception as fb_e:
            log_agent_exc("LLM", fb_e, tool="record_transaction", stage="fallback_parse", input=user_message[:40])
            raise
    return json.dumps(AccountingResult.model_validate(result).model_dump(), ensure_ascii=False)


@agent_tool(
    name="greeting_polish",
    description="Polish a short greeting reply. Not used by main router.",
    tags=("greeting",),
    routed=False,
)
def run_greeting_polish(
    user_message: str, llm, llm_model: str, llm_base_url: str, extra_hint: str = ""
) -> str:
    print(f"[LLM] tool=greeting_polish model={llm_model}")
    raw = extract_content(llm.invoke(prompt.build_greeting_prompt(user_message, extra_hint)))
    return TextReply(reply=raw or DEFAULT_CHAT_REPLY).reply
