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
    - 已有 record_id：Tool 已写库，只挂聊天卡片
    - money > 0 且无 record_id：兼容旧路径，经 expense_service 写入
    - 否则：仅保存文本回复
    """
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
