import re
from dataclasses import dataclass
from datetime import date, timedelta
from difflib import SequenceMatcher

from account.models import TransactionRecord
from django.db.models import Sum


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
    非寒暄：走后续 skill 向量 + agent 流程。
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


def fmt_amount(v):
    """金额格式化：3000.00 -> 3000，3000.50 -> 3000.5"""
    try:
        n = float(v)
        if n.is_integer():
            return str(int(n))
        return ("%s" % n).rstrip("0").rstrip(".")
    except Exception:
        return str(v)


def format_formula(amounts):
    """把金额列表转成 200 + 300 + 500 这种算式字符串"""
    if not amounts:
        return ""
    return " + ".join([fmt_amount(a) for a in amounts])


def get_last_month_summary(user) -> str:
    """
    查询用户最近一个月的收支数据，返回拼接好的文字供 AI 参考。
    包含：笔数、总额、算式明细。
    """
    try:
        today = date.today()
        start = today - timedelta(days=30)
        records = TransactionRecord.objects.filter(
            user=user,
            date__gte=start,
            date__lte=today,
        ).select_related("category")

        if not records.exists():
            return "最近一个月暂无账单记录。"

        expense_qs = records.filter(type="expense").order_by("date", "time", "id")
        income_qs = records.filter(type="income").order_by("date", "time", "id")

        total_expense = expense_qs.aggregate(s=Sum("amount"))["s"] or 0
        total_income = income_qs.aggregate(s=Sum("amount"))["s"] or 0

        income_amounts = list(income_qs.values_list("amount", flat=True)[:20])
        expense_amounts = list(expense_qs.values_list("amount", flat=True)[:20])

        income_formula = format_formula(income_amounts)
        expense_formula = format_formula(expense_amounts)

        cat_stats = (
            expense_qs.values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        cat_lines = [f"  {s['category__name']}: {fmt_amount(s['total'])}元" for s in cat_stats]

        lines = [
            f"统计周期：{start} 至 {today}",
            f"收入笔数：{income_qs.count()}笔",
            f"支出笔数：{expense_qs.count()}笔",
            f"总收入：{fmt_amount(total_income)}元",
            f"总支出：{fmt_amount(total_expense)}元",
            f"净结余：{fmt_amount(total_income - total_expense)}元",
            f"收入算式：{income_formula if income_formula else '无收入记录'} = {fmt_amount(total_income)}",
            f"支出算式：{expense_formula if expense_formula else '无支出记录'} = {fmt_amount(total_expense)}",
        ]
        if cat_lines:
            lines.append("各分类支出：")
            lines.extend(cat_lines)

        return "\n".join(lines)
    except Exception as e:
        print(f"查询账单失败: {e}")
        return "账单数据查询失败，请稍后再试。"
