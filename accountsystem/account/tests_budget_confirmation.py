from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from account.ai.agents.supervisor.budget.budget_agent import _to_graph_input
from account.ai.agents.supervisor.budget.budget_nodes import human_confirm_node
from account.ai.orchestrator import executor
from account.ai.orchestrator.task_schema import WorkflowPlan, WorkflowTask


class BudgetConfirmationTests(SimpleTestCase):
    def test_budget_confirm_input_preserves_parameters(self):
        state = _to_graph_input(
            {
                "input": "确认预算",
                "history": [],
                "user": None,
                "confirm": {"confirm": True, "confirmed_plan": True},
                "task_input": {
                    "action": "update",
                    "amount": 5000,
                    "period": "2026-09",
                    "budget_type": "month",
                    "is_total": True,
                },
            }
        )
        self.assertTrue(state["confirmed"])
        self.assertEqual(state["intent"], "set_budget")
        self.assertEqual(state["budget_params"]["amount"], 5000)

    def test_budget_confirmation_contains_write_payload(self):
        result = human_confirm_node(
            {
                "intent": "set_budget",
                "budget_params": {
                    "amount": 5000,
                    "period": "2026-09",
                    "budget_type": "month",
                    "is_total": True,
                    "category": None,
                },
                "confirmed": False,
            }
        )
        self.assertTrue(result["result"]["data"]["need_confirm"])
        self.assertEqual(result["result"]["data"]["payload"]["amount"], 5000)

    def test_multi_agent_plan_dispatches_in_dependency_order(self):
        calls = []

        def runner(name):
            def invoke(*args, **kwargs):
                calls.append(name)
                return {"output": name, "intermediate_steps": []}

            return invoke

        state = {"user_input": "组合任务", "memory_messages": [], "confirm": {"confirmed_plan": True}}
        plan = WorkflowPlan(
            tasks=[
                WorkflowTask(id="invoice", type="invoice", goal="查询发票"),
                WorkflowTask(id="asset", type="asset", goal="查询资产", depends_on=["invoice"]),
                WorkflowTask(id="budget", type="budget", goal="查询预算", depends_on=["asset"]),
                WorkflowTask(id="bill", type="bill", goal="查询账单", depends_on=["budget"]),
            ]
        )
        with patch.object(
            executor,
            "_RUNNERS",
            {name: runner(name) for name in ("bill", "budget", "asset", "invoice")},
        ):
            executor.execute_plan(state, plan)
        self.assertEqual(calls, ["invoice", "asset", "budget", "bill"])
