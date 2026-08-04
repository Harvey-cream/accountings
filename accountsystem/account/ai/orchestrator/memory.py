"""会话记忆：从 LangchainChatMessage 取最近 3 轮；更早对话后台压缩。

热路径不调 LLM：只用最近 3 轮 + 缓存摘要。
超过 3 轮时在后台线程压缩并写入 cache，供后续请求使用（不阻塞本轮 Agent/接口）。
"""

from __future__ import annotations

import threading

from django.core.cache import cache
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content, log_agent_exc
from account.models import LangchainChatMessage

RECENT_ROUNDS = 3
_FETCH_LIMIT = 40
_CACHE_TTL = 60 * 60 * 24
_compress_lock = threading.Lock()
_compressing: set[str] = set()


def load_chat_memory(user, current_input: str = "") -> tuple[list[BaseMessage], str]:
    """
    返回 (喂给子 Agent 的历史 messages, 喂给 Supervisor 的短文本)。
    无 user / 无历史时返回 ([], "")。压缩不在本函数内同步等待。
    """
    if user is None:
        return [], ""

    rows = list(
        LangchainChatMessage.objects.filter(user=user)
        .order_by("-create_time", "-id")[:_FETCH_LIMIT]
    )
    rows.reverse()

    current = (current_input or "").strip()
    if (
        rows
        and rows[-1].role == "user"
        and (rows[-1].content or "").strip() == current
    ):
        rows = rows[:-1]

    if not rows:
        return [], ""

    turns = _group_turns(rows)
    if len(turns) > RECENT_ROUNDS:
        older, recent = turns[:-RECENT_ROUNDS], turns[-RECENT_ROUNDS:]
    else:
        older, recent = [], turns

    summary = ""
    if older:
        upto_id = _last_msg_id(older)
        cache_key = _cache_key(user.id)
        cached = cache.get(cache_key) or {}
        if cached.get("upto_id") == upto_id and cached.get("summary"):
            summary = cached["summary"]
        else:
            # 本轮可用旧摘要（若有）；刷新丢到后台，不阻塞
            summary = (cached.get("summary") or "").strip()
            older_blob = _turns_blob(older)
            if len(older_blob) <= 120:
                summary = older_blob.replace("\n", "；")
                cache.set(
                    cache_key,
                    {"summary": summary, "upto_id": upto_id},
                    _CACHE_TTL,
                )
            else:
                _schedule_compress(user.id, older_blob, upto_id)

    messages: list[BaseMessage] = []
    if summary:
        messages.append(HumanMessage(content=f"[此前对话摘要] {summary}"))

    for turn in recent:
        for row in turn:
            text = (row.content or "").strip()
            if not text:
                continue
            if row.role == "user":
                messages.append(HumanMessage(content=text))
            else:
                messages.append(AIMessage(content=text))

    router_text = _router_context(summary, recent)
    return messages, router_text


def _cache_key(user_id) -> str:
    return f"ai_chat_mem_summary:{user_id}"


def _last_msg_id(turns: list[list]) -> int:
    last = turns[-1][-1]
    return int(getattr(last, "id", 0) or 0)


def _group_turns(rows: list) -> list[list]:
    turns: list[list] = []
    buf: list = []
    for row in rows:
        if row.role == "user" and buf:
            turns.append(buf)
            buf = [row]
        else:
            buf.append(row)
    if buf:
        turns.append(buf)
    return turns


def _turn_text(turn: list) -> str:
    parts = []
    for row in turn:
        label = "用户" if row.role == "user" else "助手"
        text = (row.content or "").strip()
        if text:
            parts.append(f"{label}：{text}")
    return "\n".join(parts)


def _turns_blob(turns: list[list]) -> str:
    return "\n".join(t for t in (_turn_text(turn) for turn in turns) if t)


def _schedule_compress(user_id, older_blob: str, upto_id: int) -> None:
    key = _cache_key(user_id)
    with _compress_lock:
        if key in _compressing:
            return
        _compressing.add(key)

    def _job():
        try:
            summary = _compress_blob(older_blob)
            if summary:
                cache.set(
                    key,
                    {"summary": summary, "upto_id": upto_id},
                    _CACHE_TTL,
                )
        except Exception as e:
            log_agent_exc("MEMORY", e, user_id=user_id)
        finally:
            with _compress_lock:
                _compressing.discard(key)

    threading.Thread(target=_job, name=f"mem-compress-{user_id}", daemon=True).start()


def _compress_blob(blob: str) -> str:
    if not blob:
        return ""
    if len(blob) <= 120:
        return blob.replace("\n", "；")
    raw = extract_content(
        llm.invoke(
            "将下列历史对话压成不超过80字的中文摘要，保留金额、分类、账单意图等关键事实，不要客套：\n\n"
            + blob[:2000]
        )
    )
    return (raw or "").strip()[:120] or blob[:120].replace("\n", "；")


def _router_context(summary: str, recent: list[list]) -> str:
    parts = []
    if summary:
        parts.append(f"摘要：{summary}")
    recent_text = "\n".join(t for t in (_turn_text(turn) for turn in recent) if t)
    if recent_text:
        parts.append(recent_text)
    return "\n".join(parts)[:800]
