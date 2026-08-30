from unittest.mock import patch

from django.test import SimpleTestCase
from pydantic import ValidationError

from account.ai.orchestrator.task_schema import WorkflowTask
from account.ai.orchestrator.unified_planner import RoutePlan, build_route_plan


class UnifiedPlannerTests(SimpleTestCase):
    def test_route_plan_is_task_collection(self):
        bill = WorkflowTask(id="bill", type="bill", goal="记录晚饭30元")
        budget = WorkflowTask(id="budget", type="budget", goal="设置预算7500元")

        self.assertEqual(len(RoutePlan(tasks=[bill]).tasks), 1)
        self.assertEqual(len(RoutePlan(tasks=[bill, budget]).tasks), 2)
        self.assertEqual(
            RoutePlan(
                tasks=[WorkflowTask(id="analysis", type="open_planning", goal="分析消费趋势")]
            ).tasks[0].type,
            "open_planning",
        )

    def test_route_plan_rejects_empty_or_invalid_dependencies(self):
        bill = WorkflowTask(id="bill", type="bill", goal="记录晚饭30元")
        with self.assertRaises(ValidationError):
            RoutePlan(tasks=[])
        with self.assertRaises(ValidationError):
            RoutePlan(tasks=[WorkflowTask(id="budget", type="budget", goal="预算", depends_on=["missing"])])

    def test_budget_input_uses_explicit_amount_not_year(self):
        plan = RoutePlan(
            tasks=[
                WorkflowTask(
                    id="budget",
                    type="budget",
                    goal="更新本月总预算",
                    input={"amount": 7900, "budget_type": "month", "period": "2026-08", "is_total": True},
                )
            ]
        )

        self.assertEqual(plan.tasks[0].input["amount"], 7900)
        self.assertEqual(plan.tasks[0].input["period"], "2026-08")


        expected = RoutePlan(
            tasks=[
                WorkflowTask(id="meals", type="bill", goal="记录早饭20元和晚饭30元"),
                WorkflowTask(id="budget", type="budget", goal="设置总预算7500元"),
            ],
        )
        with patch("account.ai.orchestrator.unified_planner.llm") as mock_llm:
            mock_planner = mock_llm.with_structured_output.return_value
            mock_planner.invoke.return_value = expected
            actual = build_route_plan("早饭20，晚饭30预算7500")

        self.assertEqual(actual, expected)
        mock_llm.with_structured_output.assert_called_once_with(
            RoutePlan, method="function_calling"
        )
        mock_planner.invoke.assert_called_once()
