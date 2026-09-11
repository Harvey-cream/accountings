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
                    action="batch_create",
                    goal="记录早饭和晚饭支出",
                    input={
                        "items": [
                            {"amount": 80, "description": "早饭", "category": "餐饮", "bill_type": "expense"},
                            {"amount": 30, "description": "晚饭", "category": "餐饮", "bill_type": "expense"},
                        ]
                    },                ),
                WorkflowTask(
                    id="budget",
                    type="budget",
                    action="set_budget",
                    goal="更新本月总预算",
                    input={
                        "amount": 7900,
                        "budget_type": "month",
                        "period": "2026-08",
                        "category": None,
                        "is_total": True,
                    },                ),
            ]
        )

        confirmation = _build_plan_confirmation(plan.tasks)

        self.assertEqual(
            [item["entity"] for item in confirmation["confirmations"]],
            ["bill", "budget"],
        )
        self.assertEqual(confirmation["confirmations"][0]["candidates"][0]["amount"], 80)
        self.assertEqual(confirmation["confirmations"][0]["candidates"][1]["description"], "晚饭")
        self.assertEqual(confirmation["confirmations"][1]["payload"]["amount"], 7900)
        self.assertEqual(confirmation["confirmations"][1]["payload"]["period"], "2026-08")

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
                WorkflowTask(id="bill", type="bill", action="create", goal="记录晚饭30元", input={"amount": 30}),
                WorkflowTask(id="budget", type="budget", action="set_budget", goal="设置预算7500元", input={"amount": 7500, "period": "2026-09", "budget_type": "month"}),
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
