from unittest.mock import patch

from django.test import SimpleTestCase
from pydantic import ValidationError

from account.ai.orchestrator.task_schema import WorkflowTask
from account.ai.orchestrator.unified_planner import RoutePlan, build_route_plan


class UnifiedPlannerTests(SimpleTestCase):
    def test_route_plan_is_task_collection(self):
        bill = WorkflowTask(id="bill", type="bill", action="create", goal="记录晚饭30元", input={"amount": 30})
        budget = WorkflowTask(id="budget", type="budget", action="set_budget", goal="设置预算7500元", input={"amount": 7500, "period": "2026-09", "budget_type": "month"})

        self.assertEqual(len(RoutePlan(tasks=[bill]).tasks), 1)
        self.assertEqual(len(RoutePlan(tasks=[bill, budget]).tasks), 2)
        self.assertEqual(
            RoutePlan(
                tasks=[WorkflowTask(id="analysis", type="open_planning", action="analyze", goal="分析消费趋势", input={"topic": "消费趋势"})]
            ).tasks[0].type,
            "open_planning",
        )

    def test_route_plan_rejects_empty_or_invalid_dependencies(self):
        bill = WorkflowTask(id="bill", type="bill", action="create", goal="记录晚饭30元", input={"amount": 30})
        with self.assertRaises(ValidationError):
            RoutePlan(tasks=[])
        with self.assertRaises(ValidationError):
            RoutePlan(tasks=[WorkflowTask(id="budget", type="budget", action="set_budget", goal="预算", input={"amount": 1, "period": "2026-09", "budget_type": "month"}, depends_on=["missing"])])

    def test_task_requires_action_and_action_specific_input(self):
        with self.assertRaises(ValidationError):
            WorkflowTask(type="bill", id="bill", input={"amount": 10})
        with self.assertRaises(ValidationError):
            WorkflowTask(type="budget", id="budget", action="delete", input={})
        with self.assertRaises(ValidationError):
            WorkflowTask(type="budget", id="budget", action="set_budget", input={"period": "2026-09"})

        plan = RoutePlan(
            tasks=[
                WorkflowTask(
                    id="budget",
                    type="budget",
                    action="set_budget",
                    goal="更新本月总预算",
                    input={"amount": 7900, "budget_type": "month", "period": "2026-08", "is_total": True},
                )
            ]
        )

        self.assertEqual(plan.tasks[0].input["amount"], 7900)
        self.assertEqual(plan.tasks[0].input["period"], "2026-08")


        expected = RoutePlan(
            tasks=[
                WorkflowTask(id="meals", type="bill", action="batch_create", goal="记录早饭20元和晚饭30元", input={"items": [{"amount": 20}, {"amount": 30}]}),
                WorkflowTask(id="budget", type="budget", action="set_budget", goal="设置总预算7500元", input={"amount": 7500, "period": "2026-09", "budget_type": "month"}),
            ],
        )
        with patch("account.ai.orchestrator.unified_planner.planner_llm") as mock_llm:
            mock_planner = mock_llm.with_structured_output.return_value
            mock_planner.invoke.return_value = expected
            actual = build_route_plan("早饭20，晚饭30预算7500")

        self.assertEqual(actual, expected)
        mock_llm.with_structured_output.assert_called_once_with(
            RoutePlan, method="function_calling"
        )
        mock_planner.invoke.assert_called_once()
