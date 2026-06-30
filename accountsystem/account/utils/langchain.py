from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from config.dotenv_loader import env_str

from .embedding import build_embeddings
from .func import get_last_month_summary, quick_agent_greeting_prompt
from .llm_utils import extract_content, first_tool_call, log_agent_exc
from .prompt import ROUTER_SYSTEM, build_polish_prompt
from .schemas import (
    AGENT_ERROR_REPLY,
    AccountingResult,
    DEFAULT_CHAT_REPLY,
    TextReply,
    UserMessageInput,
    accounting_response,
    chat_response,
)
from .tools import (
    ToolRunContext,
    build_bindable_tools,
    fallback_tool_name,
    run_routed_tool,
    run_greeting_polish,
)
from .vector_chroma import build_chroma_from_documents

LLM_AGENT_BASE_URL = env_str("LLM_AGENT_BASE_URL", "https://gpt-agent.cc/v1")
LLM_AGENT_API_KEY = env_str("LLM_AGENT_API_KEY")
LLM_AGENT_MODEL = env_str("LLM_AGENT_MODEL", "gpt-5.4")

if not LLM_AGENT_API_KEY:
    print("[WARN] LLM_AGENT_API_KEY 未设置，请在 accountsystem/.env 中配置（可复制 .env.example）")

llm = ChatOpenAI(
    model_name=LLM_AGENT_MODEL,
    openai_api_base=LLM_AGENT_BASE_URL,
    openai_api_key=LLM_AGENT_API_KEY,
    request_timeout=30,
    temperature=0.2,
)

KB_DOCS = [
    Document(page_content="怎么手动记账：打开APP→点击底部‘记账’→选择收入或支出→填写金额、分类、备注→保存即可。", metadata={"title": "怎么手动记账"}),
    Document(page_content="怎么用AI对话记账：在聊天框输入一句话，例如‘喝奶茶花了15元’，AI会自动识别并记账。", metadata={"title": "怎么用AI对话记账"}),
    Document(page_content="分类说明：支出分类有餐饮、购物、交通、娱乐、医疗、教育、住房、通讯、零食、其他；收入分类有工资、奖金、兼职、理财、红包、退款、其他。", metadata={"title": "分类说明"}),
    Document(page_content="软件功能：支持AI记账、手动记账、账单统计、账单查询、预算管理。", metadata={"title": "功能介绍"}),
    Document(page_content="福娃鸭人设：可爱、亲切、幽默，会用emoji，会鼓励用户好好记账。", metadata={"title": "福娃鸭人设"}),
]

_kb_vector_store = None


def _get_kb_vector_store():
    global _kb_vector_store
    if _kb_vector_store is None:
        _kb_vector_store = build_chroma_from_documents(
            "account_kb_docs", KB_DOCS, build_embeddings()
        )
    return _kb_vector_store


def _retrieve_kb_context(text: str, top_k: int = 2) -> str:
    try:
        docs = _get_kb_vector_store().similarity_search(text, k=top_k)
        return "\n".join(d.page_content for d in docs)
    except Exception as e:
        log_agent_exc("KB", e, query=text[:40])
        return ""


def _tool_context(user) -> ToolRunContext:
    return ToolRunContext(
        user=user,
        llm=llm,
        retrieve_kb=_retrieve_kb_context,
        get_summary=get_last_month_summary,
        llm_model=LLM_AGENT_MODEL,
        llm_base_url=LLM_AGENT_BASE_URL,
    )


def _parse_tool_result(text: str) -> dict | None:
    if not (isinstance(text, str) and text.startswith("{") and '"money"' in text):
        return None
    try:
        return accounting_response(AccountingResult.model_validate_json(text))
    except Exception:
        return None


def _polish_reply(user_input: str, tool_name: str, tool_result: str, fallback: str) -> str:
    try:
        raw = extract_content(
            llm.invoke(build_polish_prompt(user_input, tool_name, tool_result))
        )
        return TextReply(reply=(raw or fallback).strip()).reply
    except Exception as e:
        log_agent_exc("POLISH", e, tool=tool_name, input=user_input[:40])
        return fallback


def _finalize_output(user_input: str, tool_name: str, result_text: str) -> dict:
    parsed = _parse_tool_result(result_text)
    if parsed:
        facts = AccountingResult.model_validate(parsed)
        fallback = facts.reply or f"已记下{facts.category}{facts.money:g}元～"
        polished = _polish_reply(
            user_input, tool_name, facts.model_dump_json(ensure_ascii=False), fallback
        )
        return accounting_response(facts.model_copy(update={"reply": polished}))
    fallback = (result_text or "").strip() or DEFAULT_CHAT_REPLY
    return chat_response(_polish_reply(user_input, tool_name, result_text, fallback))


def _invoke_via_function_calling(user_input: str, user) -> dict:
    ctx = _tool_context(user)
    print(f"[FC] start input={user_input[:60]!r} user_id={getattr(user, 'id', None)}")
    try:
        tools = build_bindable_tools(ctx)
        print(f"[FC] bindable_tools={[t.name for t in tools]}")
        llm_tools = llm.bind_tools(tools)
    except Exception as e:
        log_agent_exc("FC", e, stage="bind_tools", input=user_input[:40])
        raise

    messages = [
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=user_input),
    ]

    try:
        print(f"[FC] invoking model={LLM_AGENT_MODEL}")
        ai_msg = llm_tools.invoke(messages)
        call = first_tool_call(ai_msg)
        if call:
            name, args = call
            user_message = UserMessageInput.model_validate(
                {"user_message": args.get("user_message") or user_input}
            ).user_message
            print(f"[FC] tool={name!r} args.user_message={user_message[:40]!r}...")
            result_text = run_routed_tool(name, user_message, ctx)
            return _finalize_output(user_message, name, result_text)

        reply = extract_content(ai_msg).strip()
        print("[FC] no tool_calls, direct reply")
        return chat_response(reply or DEFAULT_CHAT_REPLY)
    except Exception as e:
        log_agent_exc("FC", e, stage="invoke", input=user_input[:40])
        name = fallback_tool_name(user_input)
        print(f"[FC] tag fallback tool={name!r}")
        if name:
            try:
                result_text = run_routed_tool(name, user_input, ctx)
                return _finalize_output(user_input, name, result_text)
            except Exception as fb_e:
                log_agent_exc("FC", fb_e, stage="fallback", tool=name, input=user_input[:40])
                raise
        return chat_response(DEFAULT_CHAT_REPLY)


def _run_agent(user_input: str, user=None) -> dict:
    print(f"[AGENT] start input={user_input[:60]!r} user_id={getattr(user, 'id', None)}")
    g = quick_agent_greeting_prompt(user_input)
    if g.is_greeting:
        print(f"[ROUTE] greeting matched_as={g.matched_as!r}")
        reply = run_greeting_polish(
            user_input, llm, LLM_AGENT_MODEL, LLM_AGENT_BASE_URL, g.prompt
        )
        return chat_response(reply)

    return _invoke_via_function_calling(user_input, user)


def extract_accounting_info(text, user=None):
    try:
        return _run_agent(text, user=user)
    except Exception as e:
        log_agent_exc("AGENT", e, input=(text or "")[:60])
        out = chat_response(AGENT_ERROR_REPLY)
        out["remark"] = text
        return out


def prewarm_runtime():
    try:
        _get_kb_vector_store()
        print("[PREWARM] kb vectors ready")
    except Exception as e:
        print(f"[PREWARM] skipped: {e}")
