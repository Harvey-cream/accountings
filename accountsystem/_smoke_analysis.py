import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from account.ai.agents.supervisor.analysis.analysis_agent import _graph_to_result, _to_graph_input
from account.ai.agents.supervisor.analysis.analysis_graph import build_analysis_graph
from account.ai.agents.supervisor.analysis.analysis_router import route_after_params


class FakeUser:
    id = 1


g = build_analysis_graph(FakeUser())
nodes = sorted(g.get_graph().nodes)
assert "parameter_normalize" in nodes and "insight_generate" in nodes
print("nodes:", nodes)

assert route_after_params({"parameters": {"need_input": True}}) == "end"
assert route_after_params({"parameters": {"days": 30}}) == "analysis_agent"

inp = _to_graph_input({"input": "本月花了多少", "history": [], "user": FakeUser()})
assert inp["input"] == "本月花了多少"
out = _graph_to_result({"messages": [], "final_response": "洞察"})
assert out["output"] == "洞察"
print("ALL PASS")
