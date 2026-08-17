"""一次性联调脚本：确认卡片完整往返（模拟 view 的存消息顺序）。不参与业务运行。"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accountsystem.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django  # noqa: E402

django.setup()

from user.models import User  # noqa: E402

from account.ai.llm.response import to_api_dict  # noqa: E402
from account.ai.orchestrator import run_orchestrator  # noqa: E402
from account.models import LangchainChatMessage  # noqa: E402
from account.services import asset_service, expense_service  # noqa: E402
from account.services.langchain_chat import (  # noqa: E402
    create_ai_chat_message,
    create_user_chat_message,
    parse_confirm_payload,
)

failures = []


def check(name, ok, detail=""):
    print(("  OK   " if ok else "  FAIL ") + name + (f"  {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def turn(user, content, confirm=None):
    """完整复刻 LangchainChatView.post 的一轮：先存用户消息，再跑 Agent，再存 AI 消息。"""
    create_user_chat_message(user, content)
    ai_data = to_api_dict(run_orchestrator(content, user=user, confirm=confirm))
    create_ai_chat_message(user, content, ai_data)
    return ai_data


user = User.objects.first()
temp_user = None
if user is None:
    temp_user = User.objects.create(username="__confirm_user__")
    user = temp_user
LangchainChatMessage.objects.filter(user=user).delete()

print("\n[A] 批量记账：解析 -> 汇总确认 -> 确认后批量落库")
try:
    a1 = turn(user, "早饭10，午饭25，晚饭30")
    check("出汇总确认卡", a1.get("need_confirm") is True, a1.get("reply"))
    check("entity=bill", a1.get("confirm_entity") == "bill")
    check("action=batch_create", a1.get("confirm_action") == "batch_create")
    check("草稿 3 笔", len(a1.get("candidates") or []) == 3)
    check("确认前未落库", len(expense_service.search_expense(user, keyword="饭", days=1)) == 0)

    payload = {"confirm": True, "entity": a1["confirm_entity"], "action": a1["confirm_action"]}
    confirm = parse_confirm_payload(payload)
    check("回传解析成功", confirm is not None, str(confirm))

    a2 = turn(user, "确认", confirm=confirm)
    check("确认后不再要确认", not a2.get("need_confirm"), a2.get("reply"))
    rows = expense_service.query_expense(user, days=1, limit=50)
    check("落库 3 笔", len(rows) == 3, str([(r["amount"], r["remark"]) for r in rows]))
    check("合计 65", sum(r["amount"] for r in rows) == 65.0, str(sum(r["amount"] for r in rows)))
    for r in rows:
        expense_service.delete_expense(user, r["id"])
except Exception as e:
    check("批量往返", False, repr(e))

LangchainChatMessage.objects.filter(user=user).delete()

print("\n[B] 资产删除：定位 -> 确认卡片 -> 确认后删除")
acc = asset_service.create_asset_account(user, name="__confirm招行__", asset_type="储蓄卡", balance=888)
try:
    b1 = turn(user, "把 __confirm招行__ 这个账户删了")
    check("出确认卡", b1.get("need_confirm") is True, b1.get("reply"))
    check("entity=asset", b1.get("confirm_entity") == "asset", str(b1.get("confirm_entity")))
    check("action=delete", b1.get("confirm_action") == "delete")
    cands = b1.get("candidates") or []
    check("候选带 id", bool(cands) and cands[0].get("id") == acc["id"], str(cands))
    check("确认前未删除", len(asset_service.search_asset_accounts(user, name="__confirm招行__")) == 1)

    confirm = parse_confirm_payload(
        {
            "confirm": True,
            "entity": b1["confirm_entity"],
            "action": b1["confirm_action"],
            "target_id": cands[0]["id"],
        }
    )
    check("回传解析成功", confirm is not None, str(confirm))

    b2 = turn(user, "确认", confirm=confirm)
    check("确认后不再要确认", not b2.get("need_confirm"), b2.get("reply"))
    check("账户已删除", len(asset_service.search_asset_accounts(user, name="__confirm招行__")) == 0)
except Exception as e:
    check("资产往返", False, repr(e))
finally:
    for row in asset_service.search_asset_accounts(user, name="__confirm招行__"):
        asset_service.delete_asset_account(user, row["id"])

print("\n[C] 取消分支")
c = parse_confirm_payload({"confirm": False})
out = run_orchestrator("取消", user=user, confirm=c)
check("取消短路", "取消" in (out.get("output") or ""), out.get("output"))

LangchainChatMessage.objects.filter(user=user).delete()
if temp_user is not None:
    temp_user.delete()

print("\n结果：" + ("全部通过" if not failures else f"{len(failures)} 项失败 -> {failures}"))
sys.exit(1 if failures else 0)
