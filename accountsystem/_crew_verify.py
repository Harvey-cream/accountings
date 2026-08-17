"""Temporary verification script for the dynamic Finance Planner Crew."""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accountsystem.settings")
django.setup()

from account.ai.agents.crew.finance_planner import planner  # noqa: E402
from account.ai.agents.crew.finance_planner.crew import run_finance_planner  # noqa: E402
from account.ai.agents.crew.finance_planner.planner_schema import TaskSpec  # noqa: E402
from account.ai.llm.response import to_api_dict  # noqa: E402
from account.ai.orchestrator.open_task_router import is_probably_open  # noqa: E402


def roles(specs):
    return [s.role for s in specs]


print("=== A. planner._validate (simulated LLM outputs) ===")
case1 = {"tasks": [
    {"role": "financial_analyst", "goal": "g"},
    {"role": "budget_planner", "goal": "g"},
    {"role": "financial_advisor", "goal": "g"},
]}
case2 = {"tasks": [
    {"role": "financial_analyst", "goal": "g"},
    {"role": "financial_advisor", "goal": "g"},
]}
case3 = {"tasks": [
    {"role": "knowledge_researcher", "goal": "g"},
    {"role": "financial_advisor", "goal": "g"},
]}
print("case1:", roles(planner._validate(case1)))
print("case2:", roles(planner._validate(case2)))
print("case3:", roles(planner._validate(case3)))

print("\n=== B. hallucination / edge guards ===")
bad_role = {"tasks": [{"role": "financial_plan", "goal": "g"}]}
advisor_only = {"tasks": [{"role": "financial_advisor", "goal": "g"}]}
empty = {"tasks": []}
print("bad_role -> None?", planner._validate(bad_role) is None)
print("advisor_only -> None?", planner._validate(advisor_only) is None)
print("empty -> None?", planner._validate(empty) is None)
print("garbage -> None?", planner._validate("not a plan") is None)

advisor_middle = {"tasks": [
    {"role": "financial_advisor", "goal": "g"},
    {"role": "financial_analyst", "goal": "g"},
]}
print("advisor_middle ->", roles(planner._validate(advisor_middle)))

dupes = {"tasks": [
    {"role": "financial_analyst", "goal": "g"},
    {"role": "financial_analyst", "goal": "g2"},
    {"role": "financial_advisor", "goal": "g"},
]}
print("dupes ->", roles(planner._validate(dupes)))

print("\n=== C. default fallback plan ===")
print("default:", roles(planner._default_plan()))
filled = planner._default_plan()
print("all goals filled:", all(s.goal for s in filled))
print("all expected_output filled:", all(s.expected_output for s in filled))

print("\n=== D. no-crewai graceful degradation ===")
res = run_finance_planner("plan my year", None)
print("output:", res["output"])
print("steps:", res["intermediate_steps"])
print("has crew_result key:", "crew_result" in res)

print("\n=== E. to_api_dict compatibility with dict steps ===")
fake = {
    "output": "report text",
    "intermediate_steps": [
        {"agent": "financial_analyst", "status": "completed"},
        {"agent": "financial_advisor", "status": "completed"},
    ],
}
api = to_api_dict(fake)
print("to_api_dict ok:", api.get("reply") == "report text" or api.get("reply"))

print("\n=== F. Case4: mutation request must NOT enter Crew ===")
print("gate('delete yesterday lunch 25'):", is_probably_open("\u5220\u9664\u6628\u5929\u5348\u996525\u5143"))
print("gate('lunch 25'):", is_probably_open("\u5348\u996525"))

print("\n=== G. read-only tool whitelist ===")
from account.ai.agents.crew.finance_planner.agents import _READONLY_TOOLS, _role_tools  # noqa: E402

banned = {"create_bill", "update_bill", "delete_bill", "create_budget", "update_budget"}
print("whitelist:", sorted(_READONLY_TOOLS))
print("no banned in whitelist:", not (banned & _READONLY_TOOLS))
print("advisor tools:", _role_tools("financial_advisor", None))
