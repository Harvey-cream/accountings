"""Budget 参数与周期格式的确定性校验（不调 LLM、不碰 ORM）。"""

from __future__ import annotations

import re

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_YEAR_RE = re.compile(r"^\d{4}$")


def validate_budget_params(intent: str, params: dict) -> dict:
    """
    返回 validation_result:
      {ok: bool, need_input: bool, message: str, params: dict}
    """
    p = dict(params or {})
    budget_type = (p.get("budget_type") or "month").strip().lower()
    if budget_type not in ("month", "year"):
        budget_type = "month"
    p["budget_type"] = budget_type

    period = (p.get("period") or "").strip()
    if not period:
        return _fail(p, "请告诉我预算周期，比如本月（2026-08）或今年（2026）～")

    if budget_type == "month" and not _MONTH_RE.match(period):
        return _fail(p, '月预算周期格式应为 YYYY-MM，例如 "2026-08"～')
    if budget_type == "year" and not _YEAR_RE.match(period):
        return _fail(p, '年预算周期格式应为 YYYY，例如 "2026"～')

    if intent == "set_budget":
        amount = p.get("amount")
        if amount is None:
            return _fail(p, "请输入预算金额～")
        try:
            money = float(amount)
        except (TypeError, ValueError):
            return _fail(p, "预算金额格式不对，再说一个数字呗～")
        if money < 0:
            return _fail(p, "预算金额不能为负哦～")
        p["amount"] = money

        is_total = bool(p.get("is_total", True))
        category = (p.get("category") or "").strip() or None
        if not is_total and not category:
            return _fail(p, "设分类预算的话，请告诉我分类名，比如餐饮～")
        if is_total:
            category = None
        p["is_total"] = is_total
        p["category"] = category

    return {"ok": True, "need_input": False, "message": "", "params": p}


def _fail(params: dict, message: str) -> dict:
    return {
        "ok": False,
        "need_input": True,
        "message": message,
        "params": params,
    }
