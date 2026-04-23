import os
import json
import re
from langchain_community.chat_models import ChatOpenAI
from langchain_core.documents import Document
from dotenv import load_dotenv
from .embedding import build_embeddings
from .func import get_last_month_summary, quick_agent_greeting_prompt
from .vector_chroma import build_chroma_from_documents
from .tools import (
    _extract_content,
    tool_greeting_polish,
    tool_knowledge_rag,
    tool_query_stats,
    tool_record_extract,
)
# 主链路：Top1 Skill 提示 + 单轮「是否调工具」JSON 调度（ReAct 式意图，避免多步 text ReAct 与部分 API 不兼容）
from .prompt import output_parser, prompt_template, REACT_DECIDE_PROMPT
from .skill import ALL_TOOL_NAMES, match_best_skill, prewarm_skill_store

# 加载环境变量
load_dotenv()

# 本地与线上同一套：只认 LLM_AGENT_*。未设置环境变量时用下列默认值（私有仓库可接受）；
# 若设置了 LLM_AGENT_* / .env / yaml apply_llm_env，则优先用环境变量。
# base_url 需含 /v1。
LLM_AGENT_BASE_URL = os.getenv("LLM_AGENT_BASE_URL", "https://gpt-agent.cc/v1").strip()
LLM_AGENT_API_KEY = os.getenv("LLM_AGENT_API_KEY", "sk-dpsaFmP9J9PHpe75yyJdvQ1xkgmfIF1oPru31peFWuzPrZ6B").strip()
LLM_AGENT_MODEL = os.getenv("LLM_AGENT_MODEL", "gpt-5.4").strip()
LLM_AGENT_INSECURE_SSL = os.getenv("LLM_AGENT_INSECURE_SSL", "0").strip() == "1"

# 创建 LLM
llm = ChatOpenAI(
    model_name=LLM_AGENT_MODEL,
    openai_api_base=LLM_AGENT_BASE_URL,
    openai_api_key=LLM_AGENT_API_KEY,
    request_timeout=30,
    temperature=0.2
)

# ===== 向量 RAG 知识库（业务说明） =====
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
        embeddings = build_embeddings()
        _kb_vector_store = build_chroma_from_documents(
            "account_kb_docs", KB_DOCS, embeddings
        )
    return _kb_vector_store


def _parse_json_object(text: str) -> dict:
    t = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", t)
    if fence:
        t = fence.group(1).strip()
    s = t.find("{")
    e = t.rfind("}")
    if s == -1 or e <= s:
        raise ValueError("no JSON object in model output")
    return json.loads(t[s : e + 1])


def _decide_tool_or_reply(user_input: str, skill, llm) -> dict:
    """
    单轮 ReAct 式：模型自判是否要调工具；不调则 persona 直聊。
    解析失败时回退为「调 skill 默认 tool」，与旧链路容错一致。
    """
    prompt = REACT_DECIDE_PROMPT.format(
        skill_name=skill.name,
        skill_when=skill.when,
        skill_tool=skill.tool,
        user_input=user_input,
    )
    try:
        r = llm.invoke(prompt)
        data = _parse_json_object(_extract_content(r))
        need = bool(data.get("need_tool"))
        tool = data.get("tool")
        reply = (data.get("reply") or "").strip()
    except Exception as e:
        print(f"[REACT_DECIDE] parse failed, fallback to skill default tool: {e}")
        return {"need_tool": True, "tool": skill.tool, "reply": ""}

    if not need:
        if not reply:
            reply = "我在呀～你可以直接说「刚刚午饭25」或「这月花多少」~"
        return {"need_tool": False, "tool": None, "reply": reply}

    tname = (tool or skill.tool or "").strip()
    if tname not in ALL_TOOL_NAMES:
        tname = skill.tool
    return {"need_tool": True, "tool": tname, "reply": ""}


def _retrieve_kb_context(text: str, top_k: int = 2) -> str:
    """向量检索：按语义相似度返回最相关知识片段"""
    try:
        store = _get_kb_vector_store()
        docs = store.similarity_search(text, k=top_k)
        if not docs:
            return ""
        return "\n".join([d.page_content for d in docs])
    except Exception as e:
        print(f"知识库向量检索失败: {e}")
        return ""


def _run_agent(user_input: str, user=None) -> dict:
    """关键词/相似度寒暄；非寒暄走 Skill + 单轮路由 + 直接调 tool_*。"""
    g = quick_agent_greeting_prompt(user_input)
    if g.is_greeting:
        print(
            f"[INTENT_ROUTE] intent=greeting matched_as={g.matched_as!r} "
            f"ratio={g.best_ratio:.3f}"
        )
        result_text = tool_greeting_polish(
            user_input,
            llm,
            LLM_AGENT_MODEL,
            LLM_AGENT_BASE_URL,
            extra_system_hint=g.prompt,
        )
    else:
        print(
            f"[INTENT_ROUTE] intent=non_greeting norm={g.matched_as!r} "
            f"best_ratio={g.best_ratio:.3f}"
        )
        best_skill, skill_dist = match_best_skill(user_input)
        print(
            f"[SKILL_ROUTE] best_skill={best_skill.name!r} dist={skill_dist:.4f} "
            f"default_tool={best_skill.tool!r} model={LLM_AGENT_MODEL} base={LLM_AGENT_BASE_URL}"
        )
        decision = _decide_tool_or_reply(user_input, best_skill, llm)
        print(
            f"[REACT_DECIDE] need_tool={decision['need_tool']!r} "
            f"tool={decision.get('tool')!r} model={LLM_AGENT_MODEL} base={LLM_AGENT_BASE_URL}"
        )
        if not decision["need_tool"]:
            result_text = decision["reply"]
        elif decision["tool"] == "record_extract":
            result_text = tool_record_extract(
                user_input,
                llm,
                prompt_template,
                output_parser,
                LLM_AGENT_MODEL,
                LLM_AGENT_BASE_URL,
            )
        elif decision["tool"] == "query_stats":
            result_text = tool_query_stats(
                user_input,
                user,
                llm,
                get_last_month_summary,
                LLM_AGENT_MODEL,
                LLM_AGENT_BASE_URL,
            )
        elif decision["tool"] == "knowledge_rag":
            result_text = tool_knowledge_rag(
                user_input,
                llm,
                _retrieve_kb_context,
                LLM_AGENT_MODEL,
                LLM_AGENT_BASE_URL,
            )
        else:
            result_text = tool_record_extract(
                user_input,
                llm,
                prompt_template,
                output_parser,
                LLM_AGENT_MODEL,
                LLM_AGENT_BASE_URL,
            )

    # 统一返回格式，兼容原 views.py
    if isinstance(result_text, str) and result_text.startswith("{") and '"money"' in result_text:
        try:
            return json.loads(result_text)
        except Exception:
            pass

    return {
        "type": "支出",
        "category": "其他",
        "money": 0.0,
        "account": "其他",
        "remark": "",
        "reply": str(result_text).strip() if result_text else "我在呀～你可以直接说“刚刚午饭花了25”或“我这个月花了多少”"
    }


def extract_accounting_info(text, user=None):
    """主入口：Top1 Skill + 单轮自判是否调 tool_*；不调则仅 persona 直聊。"""
    try:
        return _run_agent(text, user=user)
    except Exception as e:
        print(f"Agent 执行失败: {str(e)}")
        return {
            "type": "支出",
            "category": "其他",
            "money": 0.0,
            "account": "其他",
            "remark": text,
            "reply": "哎呀，鸭鸭刚才走神了，没听清呢。您可以再说一遍吗？比如：'买奶茶花了15元'~"
        }


def prewarm_runtime():
    """启动预热：提前构建知识库与 Skill 向量索引（主链路已非 ReAct）。"""
    try:
        _get_kb_vector_store()
        prewarm_skill_store()
        print("[PREWARM] kb vectors + skill store ready")
    except Exception as e:
        print(f"[PREWARM] skipped due to: {e}")
