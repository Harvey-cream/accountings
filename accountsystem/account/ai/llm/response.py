import json

from .schemas import DEFAULT_CHAT_REPLY, chat_response


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


def _created_bills(steps) -> list[dict]:
    bills = []
    for action, observation in steps:
        if _tool_name(action) != "create_bill":
            continue
        payload = _parse_json(observation)
        if not payload or not payload.get("success"):
            continue
        data = payload.get("data") or {}
        if data.get("id") is None or data.get("amount") is None:
            continue
        bill_type = data.get("type") or "expense"
        type_label = "支出" if bill_type == "expense" else "收入"
        bills.append(
            {
                "type": "transaction",
                "record_id": data.get("id"),
                "icon": data.get("icon") or "notes-o",
                "payload": {
                    "type": type_label,
                    "category": data.get("category") or "其他",
                    "money": float(data.get("amount") or 0),
                    "remark": data.get("remark") or "",
                },
            }
        )
    return bills


def _budget_cards(steps) -> list[dict]:
    budgets = []
    for action, observation in steps:
        if _tool_name(action) not in {"create_budget", "update_budget"}:
            continue
        payload = _parse_json(observation)
        if not payload or not payload.get("success"):
            continue
        data = payload.get("data") or {}
        amount = data.get("amount")
        if amount is None:
            continue
        category = data.get("category") or "总预算"
        budgets.append(
            {
                "type": "budget",
                "payload": {
                    "budget_id": data.get("id"),
                    "amount": float(amount),
                    "budget_type": data.get("budget_type") or "month",
                    "period": data.get("period") or "",
                    "category": category,
                    "is_total": bool(data.get("is_total")),
                    "reply": payload.get("message") or "预算已更新",
                },
            }
        )
    return budgets


def to_api_dict(agent_result: dict) -> dict:
    steps = agent_result.get("intermediate_steps") or []
    output = (agent_result.get("output") or "").strip()

    confirm = agent_result.get("confirm") or {}
    if confirm.get("need_confirm"):
        # 扩展支持多确认项
        confirmations = confirm.get("confirmations") or []
        if not confirmations and confirm.get("prompt"):
             confirmations = [{
                 "prompt": confirm.get("prompt"),
                 "token": confirm.get("token"),
                 "payload": confirm.get("payload"),
                 "entity": confirm.get("entity", "bill"),
                 "task_id": confirm.get("task_id")
             }]

        out = chat_response(output or "确认一下这些操作吧～")
        out["need_confirm"] = True
        out["confirmations"] = confirmations
        return out

    cards = [*_created_bills(steps), *_budget_cards(steps)]
    if cards:
        return {
            "reply": output or DEFAULT_CHAT_REPLY,
            "cards": cards,
        }

    return chat_response(output or DEFAULT_CHAT_REPLY)


def chat(reply: str) -> dict:
    return chat_response(reply)
