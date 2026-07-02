"""AI 对话落库：Agent 结构化结果 → 账单记录 + 聊天消息。"""

import json
from decimal import Decimal

from django.utils import timezone

from common.initia import NORMAL_ICONS

from ..models import (
    LangchainChatMessage,
    TransactionCategory,
    TransactionIcon,
    TransactionRecord,
)


def safe_db_text(text):
    if text is None:
        return ""
    return str(text).replace("**", "")


def create_ai_chat_message(user, content, ai_data):
    """
    根据 Agent 返回的 ai_data 持久化 AI 消息：
    - money > 0：写入 TransactionRecord，消息类型为 transaction（前端账单卡片）
    - 否则：仅保存文本回复
    """
    try:
        money_val = float(ai_data.get("money", 0))
    except (TypeError, ValueError):
        money_val = 0

    if money_val > 0:
        ai_type = "transaction"
        cat_name = ai_data.get("category", "其他")
        matched_icon = next(
            (item for item in NORMAL_ICONS if item["name"] == cat_name), {"icon": "notes-o"}
        )
        record_id = None
        associated_record = None
        try:
            icon_code = matched_icon.get("icon", "notes-o")
            icon_obj = TransactionIcon.objects.filter(icon=icon_code).first()
            category_obj, _ = TransactionCategory.objects.get_or_create(
                user=user,
                name=cat_name,
                defaults={
                    "type": "expense" if ai_data.get("type") == "支出" else "income",
                    "icon": icon_obj,
                },
            )
            now = timezone.now()
            new_record = TransactionRecord.objects.create(
                user=user,
                category=category_obj,
                amount=Decimal(str(money_val)),
                type="expense" if ai_data.get("type") == "支出" else "income",
                date=now.date(),
                time=now.time(),
                remark=ai_data.get("remark", content),
            )
            record_id = new_record.id
            associated_record = new_record
        except Exception as e:
            print(f"自动记账存入失败: {e}")

        extra_data = {
            "amount": f"{'-' if ai_data.get('type') == '支出' else '+'}{money_val:.2f}",
            "category": cat_name,
            "remark": ai_data.get("remark", ""),
            "date": timezone.now().strftime("%Y年%m月%d日"),
            "icon": matched_icon.get("icon", "notes-o"),
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
