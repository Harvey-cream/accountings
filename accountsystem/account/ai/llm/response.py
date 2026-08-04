import json

from .schemas import (
    DEFAULT_CHAT_REPLY,
    AccountingResult,
    accounting_response,
    chat_response,
)


def _tool_name(action) -> str:
    if action is None:
        return ""
    if isinstance(action, dict):
        return str(action.get("name") or "")
    return str(getattr(action, "name", "") or "")


def _parse_json(raw) -> dict | None:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _last_created_bill(steps) -> dict | None:
    """从 create_bill 成功 Observation 取出账单 data。"""
    found = None
    for action, observation in steps:
        if _tool_name(action) != "create_bill":
            continue
        payload = _parse_json(observation)
        if not payload or not payload.get("success"):
            continue
        data = payload.get("data") or {}
        if data.get("id") is not None and data.get("amount") is not None:
            found = data
    return found


def to_api_dict(agent_result: dict) -> dict:
    steps = agent_result.get("intermediate_steps") or []
    output = (agent_result.get("output") or "").strip()

    bill = _last_created_bill(steps)
    if bill:
        bill_type = bill.get("type") or "expense"
        type_label = "支出" if bill_type == "expense" else "收入"
        money = float(bill.get("amount") or 0)
        category = bill.get("category") or "其他"
        remark = bill.get("remark") or ""
        reply = output or f"已记下{category}{money:g}元～"
        result = accounting_response(
            AccountingResult(
                type=type_label,
                category=category,
                money=money,
                remark=remark,
                reply=reply,
            )
        )
        result["record_id"] = bill.get("id")
        result["icon"] = bill.get("icon") or "notes-o"
        return result

    return chat_response(output or DEFAULT_CHAT_REPLY)


def chat(reply: str) -> dict:
    return chat_response(reply)
