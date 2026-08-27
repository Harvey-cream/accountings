"""一次性联调脚本：验证"多步骤 + 确认"场景下预算卡是否被吞掉。

跑法：
    cd /d D:\Code\code\accounting\accountsystem
    python _debug_multi_card_confirm.py

不参与业务运行，只做诊断。
"""

import os
import sys
import json
from pprint import pprint

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accountsystem.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django  # noqa: E402

django.setup()

from user.models import User  # noqa: E402
from account.ai.orchestrator import run_orchestrator  # noqa: E402
from account.ai.llm.response import to_api_dict  # noqa: E402
from account.services.langchain_chat import create_ai_chat_messages  # noqa: E402
from account.models import LangchainChatMessage  # noqa: E402


def dump(title, data):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    if isinstance(data, str):
        print(data)
    else:
        pprint(data, width=120, sort_dicts=False)


def dump_db_messages(user, label):
    rows = (
        LangchainChatMessage.objects
        .filter(user=user)
        .order_by("id")
        .values("id", "role", "type", "content", "extra_data")
    )
    print("\n" + "-" * 80)
    print(label)
    print("-" * 80)
    for row in rows:
        extra = row["extra_data"]
        try:
            extra = json.loads(extra) if extra else None
        except Exception:
            pass
        print({
            "id": row["id"],
            "role": row["role"],
            "type": row["type"],
            "content": row["content"],
            "extra_data": extra,
        })


def main():
    text = "早饭20，晚饭30，预算设置为7500"

    user = User.objects.first()
    if user is None:
        print("没有可用用户，请先准备一条 User 数据")
        return

    LangchainChatMessage.objects.filter(user=user).delete()

    raw = run_orchestrator(text, user=user)
    dump("1) run_orchestrator 原始返回", raw)

    api_data = to_api_dict(raw)
    dump("2) to_api_dict 给前端的返回", api_data)

    msgs = create_ai_chat_messages(user, text, api_data)
    dump(
        "3) create_ai_chat_messages 返回的消息对象",
        [f"id={m.id}, type={m.type}, content={m.content}" for m in msgs],
    )

    dump_db_messages(user, "4) 最终落库消息")

    print("\n" + "=" * 80)
    print("5) 关键判断")
    print("=" * 80)

    confirm = api_data.get("need_confirm")
    cards = api_data.get("cards") or []

    print(f"need_confirm = {confirm}")
    print(f"cards_count  = {len(cards)}")
    print(f"card_types   = {[c.get('type') for c in cards]}")

    # 额外看一眼 intermediate_steps 里到底有哪些工具
    steps = raw.get("intermediate_steps") or []
    tool_names = []
    for action, _ in steps:
        if isinstance(action, dict):
            tool_names.append(action.get("name") or "")
        else:
            tool_names.append(getattr(action, "name", "") or "")
    print(f"step_tools   = {tool_names}")

    print("-" * 80)
    if confirm and not cards:
        print("结论 A：后端走了 confirm 短路分支，cards 没有下发给前端。")
        print("       预算卡被吞掉的原因大概率在 to_api_dict 的 confirm 优先返回。")
    elif confirm and cards:
        print("结论 B：协议同时带了 confirm 和 cards，接下来要重点看前端渲染。")
    elif (not confirm) and len(cards) >= 2:
        print("结论 C：后端协议正常返回了多卡片，接下来重点看前端消息渲染/持久化。")
    else:
        print("结论 D：需要继续检查 task_planner 是否真的产出了 bill + budget 两步。")
        print("       可能 planner 压根没拆出 budget，或者 budget 这步没产生 create_budget 工具调用。")


if __name__ == "__main__":
    main()
