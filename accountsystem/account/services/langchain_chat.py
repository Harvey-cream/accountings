"""AI 对话落库：Agent 结构化结果 → 聊天消息（账单优先复用 Tool 已写入的 record）。"""

import json
from decimal import Decimal

from django.utils import timezone

from ..models import LangchainChatMessage, TransactionRecord
from .errors import ServiceError
from .expense_service import create_expense


def safe_db_text(text):
    if text is None:
        return ""
    return str(text).replace("**", "")


def create_ai_chat_message(user, content, ai_data):
    """
    根据 Agent 返回的 ai_data 持久化 AI 消息：
    - need_confirm：改删确认卡片
    - 已有 record_id：Tool 已写库，只挂聊天卡片
    - money > 0 且无 record_id：兼容旧路径，经 expense_service 写入
    - 否则：仅保存文本回复
    """
    if ai_data.get("need_confirm"):
        extra = {
            "need_confirm": True,
            "entity": ai_data.get("confirm_entity") or "bill",
            "action": ai_data.get("confirm_action") or "",
            "candidates": ai_data.get("candidates") or [],
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

    try:
        money_val = float(ai_data.get("money", 0))
    except (TypeError, ValueError):
        money_val = 0

    record_id = ai_data.get("record_id")
    associated_record = None
    icon_code = ai_data.get("icon") or "notes-o"

    if record_id:
        associated_record = TransactionRecord.objects.filter(id=record_id, user=user).first()
        if associated_record and money_val <= 0:
            money_val = float(associated_record.amount)

    if money_val > 0 or associated_record is not None:
        ai_type = "transaction"
        cat_name = ai_data.get("category", "其他")
        if associated_record is None:
            bill_type = "expense" if ai_data.get("type") == "支出" else "income"
            try:
                created = create_expense(
                    user,
                    amount=Decimal(str(money_val)),
                    bill_type=bill_type,
                    category_name=cat_name,
                    remark=ai_data.get("remark", content) or "",
                )
                record_id = created["id"]
                icon_code = created.get("icon") or icon_code
                associated_record = TransactionRecord.objects.filter(id=record_id).first()
            except ServiceError as e:
                print(f"自动记账存入失败: {e.message}")
            except Exception as e:
                print(f"自动记账存入失败: {e}")

        if associated_record is not None:
            cat_name = associated_record.category.name if associated_record.category_id else cat_name
            type_label = "支出" if associated_record.type == "expense" else "收入"
            money_val = float(associated_record.amount)
        else:
            type_label = ai_data.get("type") or "支出"

        extra_data = {
            "amount": f"{'-' if type_label == '支出' else '+'}{money_val:.2f}",
            "category": cat_name,
            "remark": ai_data.get("remark", ""),
            "date": timezone.now().strftime("%Y年%m月%d日"),
            "icon": icon_code,
            "iconColor": "#64748b",
            "bgColor": "#f1f5f9",
            "record_id": record_id,
        }
    else:
        ai_type = "text"
        extra_data = None
        associated_record = None

    return LangchainChatMessage.objects.create(
        user=user,
        role="ai",
        type=ai_type,
        content=safe_db_text(ai_data.get("reply", "")),
        extra_data=json.dumps(extra_data, ensure_ascii=False) if extra_data else None,
        record=associated_record,
    )


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
    "asset": {"create", "update", "delete", "adjust_balance"},
    "invoice": {"update", "delete"},
}
# 这些操作没有既有目标对象，回传不需要 id
_TARGETLESS_CONFIRMS = {("bill", "batch_create"), ("asset", "create")}


def resolve_confirm_card(user, message_id=None) -> bool:
    """把确认卡片标记为已处理并落库，返回 False 表示此前已处理过。

    调用方拿到 False 必须拒绝本轮执行：确认状态只存在于前端内存时，用户刷新页面
    后按钮会复活，再点一次批量记账、新建账户这类写操作就会重复落库。
    message_id 缺省时取该用户最近一张确认卡片，兼容不回传 id 的客户端。
    """
    qs = LangchainChatMessage.objects.filter(user=user, role="ai", type="confirm")
    card = (
        qs.filter(id=message_id).first()
        if message_id is not None
        else qs.order_by("-create_time", "-id").first()
    )
    if card is None:
        return True

    try:
        extra = json.loads(card.extra_data or "{}")
    except (TypeError, ValueError):
        extra = {}
    if extra.get("resolved"):
        return False

    extra["resolved"] = True
    card.extra_data = json.dumps(extra, ensure_ascii=False)
    card.save(update_fields=["extra_data"])
    return True


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
    try:
        payload["message_id"] = int(data.get("message_id"))
    except (TypeError, ValueError):
        pass
    if payload["confirm"] is False:
        return payload

    entity = (data.get("entity") or "bill").strip() or "bill"
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
