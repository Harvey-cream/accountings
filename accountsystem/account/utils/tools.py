from dataclasses import dataclass
from typing import Callable

from langchain_core.tools import StructuredTool

from . import prompt
from .llm_utils import extract_content, json_from_text, log_agent_exc
from .schemas import (
    APP_HELP_EMPTY_REPLY,
    BILL_SUMMARY_EMPTY_REPLY,
    BILL_SUMMARY_NO_USER,
    AccountingResult,
    TextReply,
    ToolObservation,
)

_RECORD_DESC = (
    "Parse the user message into one new income/expense transaction. "
    "Use when: specific amount or logging a purchase/income. "
    "Do NOT use when: asking totals like 'how much did I spend this month'."
)
_SUMMARY_DESC = (
    "Query the current user's bill summary for the last 30 days. "
    "Use when: how much spent/earned, monthly summary. "
    "Do NOT use when: logging a new transaction with an amount."
)
_HELP_DESC = (
    "Answer product/how-to questions from the knowledge base. "
    "Use when: how to use the app, features, categories. "
    "Do NOT use when: querying the user's real bill numbers."
)


@dataclass(frozen=True)
class ToolContext:
    user: object
    llm: object
    retrieve_kb: Callable[[str], str]
    get_summary: Callable


def _record(user_message: str, ctx: ToolContext) -> ToolObservation:
    p = prompt.build_record_prompt(user_message)
    try:
        structured = ctx.llm.with_structured_output(AccountingResult)
        result = structured.invoke(p)
        if isinstance(result, dict):
            result = AccountingResult.model_validate(result)
    except Exception as e:
        log_agent_exc(
            "LLM", e, tool="record_transaction", stage="structured", input=user_message[:40]
        )
        try:
            raw = extract_content(ctx.llm.invoke(p))
            result = AccountingResult.model_validate_json(json_from_text(raw))
        except Exception as fb_e:
            log_agent_exc(
                "LLM",
                fb_e,
                tool="record_transaction",
                stage="fallback_parse",
                input=user_message[:40],
            )
            return ToolObservation(
                ok=False,
                kind="record",
                error="未能解析记账信息，请补充金额或更完整的描述",
            )
    result = AccountingResult.model_validate(result)
    if result.money <= 0:
        return ToolObservation(
            ok=False,
            kind="record",
            error="未识别到有效金额，请向用户确认金额",
        )
    return ToolObservation(ok=True, kind="record", record=result)


def _summary(user_message: str, ctx: ToolContext) -> ToolObservation:
    if ctx.user is None:
        return ToolObservation(
            ok=False,
            kind="text",
            text=BILL_SUMMARY_NO_USER,
            error="missing_user",
        )
    raw = extract_content(
        ctx.llm.invoke(prompt.build_bill_summary_prompt(user_message, ctx.get_summary(ctx.user)))
    )
    while "  " in raw:
        raw = raw.replace("  ", " ")
    text = TextReply(reply=raw.strip() or BILL_SUMMARY_EMPTY_REPLY).reply
    return ToolObservation(ok=True, kind="text", text=text)


def _help(user_message: str, ctx: ToolContext) -> ToolObservation:
    kb_context = ctx.retrieve_kb(user_message) or (
        "怎么手动记账：打开APP→点击底部‘记账’→选择收入或支出→填写金额、分类、备注→保存即可。"
    )
    raw = extract_content(
        ctx.llm.invoke(prompt.build_app_help_prompt(user_message, kb_context))
    )
    text = TextReply(reply=raw or APP_HELP_EMPTY_REPLY).reply
    return ToolObservation(ok=True, kind="text", text=text)


def build_tools(ctx: ToolContext) -> list[StructuredTool]:
    def record_transaction(user_message: str) -> str:
        return _record(user_message, ctx).for_agent()

    def query_bill_summary(user_message: str) -> str:
        return _summary(user_message, ctx).for_agent()

    def answer_app_help(user_message: str) -> str:
        return _help(user_message, ctx).for_agent()

    return [
        StructuredTool.from_function(
            func=record_transaction, name="record_transaction", description=_RECORD_DESC
        ),
        StructuredTool.from_function(
            func=query_bill_summary, name="query_bill_summary", description=_SUMMARY_DESC
        ),
        StructuredTool.from_function(
            func=answer_app_help, name="answer_app_help", description=_HELP_DESC
        ),
    ]
