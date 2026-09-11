"""AI 对话落库：Agent 结构化结果 → 聊天消息（账单优先复用 Tool 已写入的 record）。"""

import json
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ..models import LangchainChatMessage, TransactionRecord
from .errors import ServiceError
from .expense_service import create_expense


def safe_db_text(text):
    if text is None:
        return ""
    return str(text)


def _create_confirm_message(user, ai_data):
    confirmations = ai_data.get("confirmations") or []
    primary = confirmations[0] if confirmations else {}
    extra = {
        "need_confirm": True,
        "entity": ai_data.get("confirm_entity") or primary.get("entity"),
        "action": ai_data.get("confirm_action") or primary.get("action") or "",
        "candidates": ai_data.get("candidates") or primary.get("candidates") or [],
        "payload": ai_data.get("payload") or primary.get("payload") or {},
        "confirmations": confirmations,
        "plan_tasks": ai_data.get("plan_tasks") or [],
        "workflow_plan": ai_data.get("workflow_plan") or ai_data.get("plan_tasks") or [],
        "trace_id": ai_data.get("trace_id") or "",
        "plan_id": ai_data.get("plan_id") or "",
        "resolved": False,
    }
    return LangchainChatMessage.objects.create(
        user=user,
        role="ai",
        type="confirm",
        content=safe_db_text(ai_data.get("reply", "")),
        extra_data=json.dumps(extra, ensure_ascii=False),
        record=None,
    )


def _create_transaction_message(user, content, card):
    payload = card.get("payload") or {}
    try:
        money_val = float(payload.get("money", 0))
    except (TypeError, ValueError):
        money_val = 0

    record_id = card.get("record_id")
    associated_record = None
    icon_code = card.get("icon") or "notes-o"

    if record_id:
        associated_record = TransactionRecord.objects.filter(id=record_id, user=user).first()
        if associated_record and money_val <= 0:
            money_val = float(associated_record.amount)

    if associated_record is None and money_val > 0:
        cat_name = payload.get("category", "其他")
        bill_type = "expense" if payload.get("type") == "支出" else "income"
        try:
            created = create_expense(
                user,
                amount=Decimal(str(money_val)),
                bill_type=bill_type,
                category_name=cat_name,
                remark=payload.get("remark", content) or "",
            )
            record_id = created["id"]
            icon_code = created.get("icon") or icon_code
            associated_record = TransactionRecord.objects.filter(id=record_id).first()
        except ServiceError as e:
            print(f"自动记账存入失败: {e.message}")
        except Exception as e:
            print(f"自动记账存入失败: {e}")

    if associated_record is not None:
        cat_name = associated_record.category.name if associated_record.category_id else payload.get("category", "其他")
        type_label = "支出" if associated_record.type == "expense" else "收入"
        money_val = float(associated_record.amount)
    else:
        cat_name = payload.get("category", "其他")
        type_label = payload.get("type") or "支出"

    extra_data = {
        "amount": f"{'-' if type_label == '支出' else '+'}{money_val:.2f}",
        "category": cat_name,
        "remark": payload.get("remark", ""),
        "date": timezone.now().strftime("%Y年%m月%d日"),
        "icon": icon_code,
        "iconColor": "#64748b",
        "bgColor": "#f1f5f9",
        "record_id": record_id,
    }
    return LangchainChatMessage.objects.create(
        user=user,
        role="ai",
        type="transaction",
        content="",
        extra_data=json.dumps(extra_data, ensure_ascii=False),
        record=associated_record,
    )


def _create_budget_message(user, card):
    payload = card.get("payload") or {}
    budget_type = "月预算" if payload.get("budget_type") == "month" else "年预算"
    category = payload.get("category") or "总预算"
    extra_data = {
        "budget_id": payload.get("budget_id"),
        "amount": f"{float(payload.get('amount') or 0):.2f}",
        "budget_type": budget_type,
        "period": payload.get("period") or "",
        "category": category,
        "is_total": bool(payload.get("is_total")),
    }
    return LangchainChatMessage.objects.create(
        user=user,
        role="ai",
        type="budget",
        content=safe_db_text(payload.get("reply", "预算已更新")),
        extra_data=json.dumps(extra_data, ensure_ascii=False),
        record=None,
    )


def create_ai_chat_messages(user, content, ai_data):
    """
    根据 Agent 返回的 ai_data 持久化 AI 消息：
    - need_confirm：改删确认卡片
    - cards：文本总结 + 多张结构化卡片
    - 兼容旧路径：单账单或纯文本
    """
    if ai_data.get("need_confirm"):
        return [_create_confirm_message(user, ai_data)]

    cards = ai_data.get("cards") or []
    messages = []
    reply = safe_db_text(ai_data.get("reply", ""))
    analysis_view = ai_data.get("analysis_view") or None
    extra_payload = None
    if analysis_view:
        extra_payload = json.dumps({"analysis_view": analysis_view}, ensure_ascii=False)
    if reply:
        messages.append(
            LangchainChatMessage.objects.create(
                user=user,
                role="ai",
                type="text",
                content=reply,
                extra_data=extra_payload,
                record=None,
            )
        )

    for card in cards:
        card_type = card.get("type")
        if card_type == "transaction":
            messages.append(_create_transaction_message(user, content, card))
        elif card_type == "budget":
            messages.append(_create_budget_message(user, card))

    if messages:
        return messages

    return [
        LangchainChatMessage.objects.create(
            user=user,
            role="ai",
            type="text",
            content=safe_db_text(ai_data.get("reply", "")),
            extra_data=None,
            record=None,
        )
    ]


def create_user_chat_message(user, content):
    """保存用户发送的一条对话消息。"""
    return LangchainChatMessage.objects.create(
        user=user,
        role="user",
        type="text",
        content=safe_db_text(content),
    )


# 各业务域允许经确认卡片回传的写操作
_CONFIRM_ACTIONS = {
    "bill": {"update", "delete", "batch_create"},
    "budget": {"set_budget", "update"},
    "asset": {"create", "update", "delete", "adjust_balance"},
    "invoice": {"update", "delete"},
}
# 这些操作没有既有目标对象，回传不需要 id
_TARGETLESS_CONFIRMS = {
    ("bill", "batch_create"),
    ("asset", "create"),
    ("budget", "set_budget"),
}


def resolve_confirm_card(user, message_id=None) -> tuple[bool, dict | None]:
    """把确认卡片标记为已处理并落库，返回 (是否可继续, extra_data)。

    调用方拿到 False 必须拒绝本轮执行：确认状态只存在于前端内存时，用户刷新页面
    后按钮会复活，再点一次批量记账、新建账户这类写操作就会重复落库。
    message_id 缺省时取该用户最近一张确认卡片，兼容不回传 id 的客户端。
    """
    with transaction.atomic():
        qs = LangchainChatMessage.objects.select_for_update().filter(
            user=user, role="ai", type="confirm"
        )
        card = (
            qs.filter(id=message_id).first()
            if message_id is not None
            else qs.order_by("-create_time", "-id").first()
        )
        if card is None:
            return False, None

        try:
            extra = json.loads(card.extra_data or "{}")
        except (TypeError, ValueError):
            return False, None
        if not isinstance(extra, dict) or extra.get("resolved"):
            return False, extra if isinstance(extra, dict) else None
        if not extra.get("workflow_plan") and not extra.get("plan_tasks") and not (
            extra.get("entity") and extra.get("action")
        ):
            return False, None

        extra["resolved"] = True
        card.extra_data = json.dumps(extra, ensure_ascii=False)
        card.save(update_fields=["extra_data"])
        return True, extra


def parse_confirm_payload(data) -> dict | None:
    """前端确认卡片回传：confirm 缺省为 None（普通对话）。

    entity 缺省为 bill，target_id 兼容旧字段 bill_id，保证老前端不受影响。
    message_id 指向那张确认卡片消息，用于落库已处理状态。
    """
    if not isinstance(data, dict) or "confirm" not in data:
        return None
    raw = data.get("confirm")
    if isinstance(raw, str):
        raw = raw.strip().lower() in ("1", "true", "yes")
    payload = {"confirm": bool(raw)}
    if "message_id" in data:
        try:
            payload["message_id"] = int(data.get("message_id"))
        except (TypeError, ValueError):
            return None
    if payload["confirm"] is False:
        return payload

    entity = data.get("entity")
    if not isinstance(entity, str) or not entity.strip():
        return None
    entity = entity.strip()
    action = (data.get("action") or "").strip()
    if action not in _CONFIRM_ACTIONS.get(entity, set()):
        return None
    payload["entity"] = entity
    payload["action"] = action

    if (entity, action) in _TARGETLESS_CONFIRMS:
        return payload
    try:
        payload["target_id"] = int(data.get("target_id", data.get("bill_id")))
    except (TypeError, ValueError):
        return None
    payload["bill_id"] = payload["target_id"]
    return payload
