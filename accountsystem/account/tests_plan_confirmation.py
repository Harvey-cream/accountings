from unittest.mock import patch

from django.test import SimpleTestCase

from account.ai.orchestrator.executor import _build_plan_confirmation
from account.ai.orchestrator.task_schema import WorkflowPlan, WorkflowTask


class PlanConfirmationTests(SimpleTestCase):
    def test_plan_confirmation_contains_bill_and_budget(self):
        plan = WorkflowPlan(
            tasks=[
                WorkflowTask(
                    id="meals",
                    type="bill",
                    goal="记录早饭20元和晚饭30元",
                ),
                WorkflowTask(
                    id="budget",
                    type="budget",
                    goal="设置总预算7500元",
                ),
            ]
        )

        confirmation = _build_plan_confirmation(plan.tasks)

        self.assertEqual(
            [item["entity"] for item in confirmation["confirmations"]],
            ["bill", "budget"],
        )
        self.assertEqual(confirmation["confirmations"][1]["payload"]["amount"], 7500.0)

    def test_confirmed_plan_does_not_require_preview_again(self):
        from account.ai.orchestrator import executor

        state = {
            "user_input": "确认",
            "user": None,
            "confirm": {"confirmed_plan": True},
            "memory_messages": [],
        }
        plan = WorkflowPlan(
            tasks=[
                WorkflowTask(id="bill", type="bill", goal="记录晚饭30元"),
                WorkflowTask(id="budget", type="budget", goal="设置预算7500元"),
            ]
        )
        with patch.object(executor, "_RUNNERS", {
            "bill": lambda *args, **kwargs: {"output": "账单完成", "intermediate_steps": []},
            "budget": lambda *args, **kwargs: {"output": "预算完成", "intermediate_steps": []},
        }):
            result = executor.execute_plan(state, plan)

        self.assertFalse(result["final_response"].get("confirm"))
        self.assertIn("账单完成", result["final_response"]["output"])
        self.assertIn("预算完成", result["final_response"]["output"])
