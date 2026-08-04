from langchain_core.documents import Document

from .embedding import build_embeddings
from account.ai.llm.llm_utils import log_agent_exc
from .vector_chroma import build_chroma_from_documents

KB_DOCS = [
    Document(
        page_content="怎么手动记账：打开APP→点击底部‘记账’→选择收入或支出→填写金额、分类、备注→保存即可。",
        metadata={"title": "怎么手动记账"},
    ),
    Document(
        page_content="怎么用AI对话记账：在聊天框输入一句话，例如‘喝奶茶花了15元’，AI会自动识别并记账。",
        metadata={"title": "怎么用AI对话记账"},
    ),
    Document(
        page_content="分类说明：支出分类有餐饮、购物、交通、娱乐、医疗、教育、住房、通讯、零食、其他；收入分类有工资、奖金、兼职、理财、红包、退款、其他。",
        metadata={"title": "分类说明"},
    ),
    Document(
        page_content="软件功能：支持AI记账、手动记账、账单统计、账单查询、预算管理。",
        metadata={"title": "功能介绍"},
    ),
    Document(
        page_content="福娃鸭人设：可爱、亲切、幽默，会用emoji，会鼓励用户好好记账。",
        metadata={"title": "福娃鸭人设"},
    ),
]

_store = None


def _get_store():
    global _store
    if _store is None:
        _store = build_chroma_from_documents(
            "account_kb_docs", KB_DOCS, build_embeddings()
        )
    return _store


def retrieve(query: str, top_k: int = 2) -> str:
    try:
        docs = _get_store().similarity_search(query, k=top_k)
        return "\n".join(d.page_content for d in docs)
    except Exception as e:
        log_agent_exc("KB", e, query=(query or "")[:40])
        return ""


def prewarm() -> None:
    try:
        _get_store()
        print("[PREWARM] kb vectors ready")
    except Exception as e:
        print(f"[PREWARM] kb skipped: {e}")
