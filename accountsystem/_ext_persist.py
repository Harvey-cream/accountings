"""一次性联调脚本：确认卡片状态持久化 + 批量记账确认往返。不参与业务运行。"""

import json
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accountsystem.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django  # noqa: E402

django.setup()

from user.models import User  # noqa: E402

from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402

from account.ai.agents.supervisor.bill.bill_nodes import _origin_text  # noqa: E402
from account.ai.llm.response import to_api_dict  # noqa: E402
from account.ai.orchestrator import run_orchestrator  # noqa: E402
from account.models import LangchainChatMessage, TransactionIcon, TransactionRecord  # noqa: E402
from account.services.langchain_chat import (  # noqa: E402
    create_ai_chat_message,
    create_user_chat_message,
    parse_confirm_payload,
    resolve_confirm_card,
)

failures = []


def check(name, ok, detail=""):
    print(("  OK   " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def card_extra(card_id):
    return json.loads(LangchainChatMessage.objects.get(id=card_id).extra_data or "{}")


def turn(user, content, confirm=None):
    """复刻 view 的一轮：先过确认闸门，再存用户消息、跑 Agent、存 AI 消息。"""
    if confirm is not None and not resolve_confirm_card(user, confirm.get("message_id")):
        return {"reply": "__ALREADY_DONE__"}
    create_user_chat_message(user, content)
    ai_data = to_api_dict(run_orchestrator(content, user=user, confirm=confirm))
    create_ai_chat_message(user, content, ai_data)
    return ai_data


user = User.objects.create(username="__persist_user__", password="x")
try:
    print("\n[1] _origin_text 只看 confirmed 布尔")
    origin = "早饭10午饭25晚饭30"
    check("未确认用本轮 input", _origin_text({
        "input": origin, "confirmed": False, "messages": [HumanMessage(content=origin)],
    }) == origin)
    check("确认后跳过占位句", _origin_text({
        "input": "确认记账",
        "confirmed": True,
        "messages": [
            HumanMessage(content=origin),
            AIMessage(content="确认都记下来吗？"),
            HumanMessage(content="确认记账"),
        ],
    }) == origin)

    print("\n[2] parse_confirm_payload 带 message_id")
    p = parse_confirm_payload({"confirm": True, "entity": "asset", "action": "delete",
                               "target_id": 7, "message_id": "42"})
    check("确认解析", p == {"confirm": True, "message_id": 42, "entity": "asset",
                            "action": "delete", "target_id": 7, "bill_id": 7}, str(p))
    p = parse_confirm_payload({"confirm": False, "message_id": 42})
    check("取消解析", p == {"confirm": False, "message_id": 42}, str(p))
    p = parse_confirm_payload({"confirm": False})
    check("无 message_id 不报错", p == {"confirm": False}, str(p))

    print("\n[3] resolve_confirm_card 幂等闸门")
    card = create_ai_chat_message(user, "x", {
        "need_confirm": True, "reply": "确认删除？", "confirm_entity": "asset",
        "confirm_action": "delete", "candidates": [{"id": 1, "name": "招行"}],
    })
    check("初始未处理", card_extra(card.id).get("resolved") is False)
    check("首次认领成功", resolve_confirm_card(user, card.id) is True)
    check("已落库 resolved", card_extra(card.id).get("resolved") is True)
    check("重复认领被拒", resolve_confirm_card(user, card.id) is False)
    check("不存在的 id 放行", resolve_confirm_card(user, 99999999) is True)

    card2 = create_ai_chat_message(user, "x", {
        "need_confirm": True, "reply": "确认删除？", "confirm_entity": "bill",
        "confirm_action": "delete", "candidates": [{"id": 2}],
    })
    check("缺省 id 认领最近一张", resolve_confirm_card(user, None) is True)
    check("最近一张已落库", card_extra(card2.id).get("resolved") is True)
    check("缺省 id 重复认领被拒", resolve_confirm_card(user, None) is False)

    print("\n[4] 批量记账确认往返（真实 LLM）")
    if TransactionIcon.objects.count() == 0:
        print("  SKIP  无图标种子数据")
    else:
        LangchainChatMessage.objects.filter(user=user).delete()
        r1 = turn(user, "帮我记一下，早饭10块，午饭25块，晚饭30块")
        drafts = r1.get("candidates") or []
        check("给出批量确认卡片", bool(r1.get("need_confirm")) and len(drafts) == 3,
              f"need_confirm={r1.get('need_confirm')} n={len(drafts)}")
        cid = LangchainChatMessage.objects.filter(user=user, type="confirm").latest("id").id

        before = TransactionRecord.objects.filter(user=user).count()
        r2 = turn(user, "确认记账", confirm={
            "confirm": True, "entity": "bill", "action": "batch_create", "message_id": cid,
        })
        created = TransactionRecord.objects.filter(user=user).count() - before
        check("确认后写入 3 笔", created == 3, f"created={created} reply={r2.get('reply')[:60]}")
        check("卡片已落库 resolved", card_extra(cid).get("resolved") is True)

        r3 = turn(user, "确认记账", confirm={
            "confirm": True, "entity": "bill", "action": "batch_create", "message_id": cid,
        })
        again = TransactionRecord.objects.filter(user=user).count() - before
        check("重复确认被拦截", r3.get("reply") == "__ALREADY_DONE__" and again == 3,
              f"total_created={again}")
finally:
    TransactionRecord.objects.filter(user=user).delete()
    LangchainChatMessage.objects.filter(user=user).delete()
    user.delete()

print("\n结果: " + ("全部通过" if not failures else f"{len(failures)} 项失败 -> {failures}"))
sys.exit(1 if failures else 0)
