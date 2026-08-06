import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from langchain_core.messages import AIMessage, HumanMessage

from account.ai.agents.supervisor.bill.bill_nodes import (
    context_prepare_node,
    human_confirm_node,
    result_formatter_node,
)
from account.ai.agents.supervisor.bill.bill_router import (
    route_after_mutation_check,
    route_by_intent,
)

history = [
    HumanMessage(content="把星巴克那笔删了"),
    AIMessage(content="确认删除2026-08-05 星巴克 25元这笔账单吗（账单#12）？回复“确认”我就去办～"),
]

print("resume:", context_prepare_node({"input": "确认", "messages": history}))
print("cold:", context_prepare_node({"input": "午饭花了25", "messages": []}))
print(
    "confirm_one:",
    human_confirm_node(
        {
            "intent": "delete",
            "candidates": [{"id": 12, "date": "2026-08-05", "remark": "星巴克", "amount": 25.0}],
        }
    )["result"]["message"],
)
print(
    "confirm_many:",
    human_confirm_node(
        {
            "intent": "update",
            "candidates": [
                {"id": 12, "date": "2026-08-05", "remark": "星巴克", "amount": 25.0},
                {"id": 15, "date": "2026-08-04", "remark": "星巴克", "amount": 32.5},
            ],
        }
    )["result"]["message"],
)
print("route create:", route_by_intent({"intent": "create"}))
print("route delete:", route_by_intent({"intent": "delete"}))
print("after_check confirm:", route_after_mutation_check({"need_confirm": True}))
print("after_check go:", route_after_mutation_check({"need_confirm": False}))
print("after_check none:", route_after_mutation_check({"result": {"message": "x"}}))
print(
    "formatter:",
    result_formatter_node({"messages": [AIMessage(content="记好啦～")], "intent": "create"}),
)
