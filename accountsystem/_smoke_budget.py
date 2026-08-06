import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from account.ai.agents.supervisor.budget.budget_agent import _graph_to_result, _to_graph_input
from account.ai.agents.supervisor.budget.budget_graph import build_budget_graph
from account.ai.agents.supervisor.budget.budget_router import route_after_policy, route_after_validator
from account.ai.agents.supervisor.budget.budget_validator import validate_budget_params


class FakeUser:
    id = 1


g = build_budget_graph(FakeUser())
nodes = sorted(g.get_graph().nodes)
assert "policy_check" in nodes and "parameter_validator" in nodes
print("nodes:", nodes)

v = validate_budget_params("set_budget", {"period": "2026-08", "budget_type": "month"})
assert v["ok"] is False and v["need_input"] is True
print("missing amount:", v["message"])

v2 = validate_budget_params(
    "set_budget",
    {"amount": 3000, "period": "2026-08", "budget_type": "month", "is_total": True},
)
assert v2["ok"] is True
print("ok params")

assert route_after_validator({"need_input": True, "validation_result": {"ok": False}}) == "end"
assert route_after_policy({"policy_result": {"ok": False}, "final_response": "x"}) == "end"
assert route_after_policy({"policy_result": {"ok": True}}) == "budget_agent"

out = _graph_to_result({"messages": [], "final_response": "预算剩余500"})
assert out["output"] == "预算剩余500"
print("ALL PASS")
