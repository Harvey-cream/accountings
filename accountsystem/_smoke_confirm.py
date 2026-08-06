import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from account.ai.agents.supervisor.bill.bill_agent import _graph_to_result, _to_graph_input
from account.ai.agents.supervisor.bill.bill_nodes import human_confirm_node
from account.ai.llm.response import to_api_dict
from account.ai.orchestrator import run_orchestrator
from account.services.langchain_chat import parse_confirm_payload


st = _to_graph_input({
    "input": "确认删除",
    "history": [],
    "user": type("U", (), {"id": 1})(),
    "confirm": {"confirm": True, "bill_id": 12, "action": "delete"},
})
assert st["confirmed"] is True and st["intent"] == "delete" and st["target_bill"]["id"] == 12
print("to_graph_input ok")

assert parse_confirm_payload({"confirm": False}) == {"confirm": False}
assert parse_confirm_payload({"confirm": True, "bill_id": 12, "action": "delete"})["bill_id"] == 12
assert parse_confirm_payload({"confirm": True, "bill_id": "x", "action": "delete"}) is None
assert parse_confirm_payload({"content": "hi"}) is None
print("parse ok")

node = human_confirm_node({
    "intent": "delete",
    "candidates": [{"id": 12, "date": "2026-08-05", "remark": "星巴克", "amount": 25, "type": "expense"}],
})
gr = _graph_to_result({"messages": node["messages"], "result": node["result"]})
api = to_api_dict(gr)
assert api["need_confirm"] is True
assert api["confirm_action"] == "delete"
assert api["candidates"][0]["id"] == 12
print("api ok")

cancel = run_orchestrator("取消", user=None, confirm={"confirm": False})
assert cancel["output"].startswith("好的")
print("cancel ok", cancel["output"])
print("ALL PASS")
