import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from account.services.expense_service import analyze_expense


# 仅极少数字典寒暄：先精确、再与字典键做相似度（避免和记账/消费句混淆）
_GREETING_EXACT: frozenset[str] = frozenset({"在吗", "你好"})

# 可扩展的别名/常见误触（短句才参与相似度）
_GREETING_ALIASES: dict[str, str] = {
    "在么": "在吗",
    "在嘛": "在吗",
    "嗨": "你好",
    "哈喽": "你好",
}

_SIMILARITY_THRESHOLD = 0.86
_MAX_LEN_FOR_GREETING = 8


@dataclass(frozen=True)
class GreetingCheck:
    is_greeting: bool
    matched_as: str
    best_ratio: float
    prompt: str


def _normalize_phrase(text: str) -> str:
    s = (text or "").strip()
    s = s.strip(" \t\r\n")
    s = re.sub(r"^[。，,、]+", "", s)
    s = re.sub(r"[！!。.，,？?~～…]+$", "", s)
    return s


def quick_agent_greeting_prompt(user_input: str) -> GreetingCheck:
    """
    用字典精确匹配 + 标准库 difflib 相似度判断是否为极短寒暄。
    非寒暄：走后续工具调度 + agent 流程。
    """
    key = _normalize_phrase(user_input)
    if not key:
        return GreetingCheck(False, "", 0.0, "")

    if any(ch.isdigit() for ch in key) or len(key) > _MAX_LEN_FOR_GREETING:
        return GreetingCheck(False, key, 0.0, "")

    if key in _GREETING_EXACT:
        p = "你是福娃鸭，用户只是在打招呼。用一句≤30字短句、亲切、带0~1个emoji回复，并顺带提一句可记账/查账。"
        return GreetingCheck(True, key, 1.0, p)

    if key in _GREETING_ALIASES:
        canon = _GREETING_ALIASES[key]
        p = "你是福娃鸭，用户只是在打招呼。用一句≤30字短句、亲切、带0~1个emoji回复，并顺带提一句可记账/查账。"
        return GreetingCheck(True, canon, 0.99, p)

    best_key = ""
    best_ratio = 0.0
    for g in _GREETING_EXACT:
        r = SequenceMatcher(None, key, g).ratio()
        if r > best_ratio:
            best_ratio = r
            best_key = g

    if best_ratio >= _SIMILARITY_THRESHOLD:
        p = f"用户输入与寒暄用语「{best_key}」高度相似。你是福娃鸭，用一句≤30字、亲切、带0~1个emoji的寒暄，并顺提可记账/查账。"
        return GreetingCheck(True, best_key, best_ratio, p)

    return GreetingCheck(False, key, best_ratio, "")


def get_last_month_summary(user) -> str:
    """
    查询用户最近一个月的收支数据，返回拼接好的文字供 AI 参考。
    委托 expense_service.analyze_expense（AI 业务能力层）。
    """
    return analyze_expense(user, days=30)
