from unittest.mock import patch

from django.test import SimpleTestCase
from pydantic import ValidationError

from account.ai.orchestrator.task_schema import WorkflowTask
from account.ai.orchestrator.unified_planner import RoutePlan, build_route_plan


class UnifiedPlannerTests(SimpleTestCase):
    def test_route_plan_validates_all_modes(self):
        bill = WorkflowTask(id="bill", type="bill", goal="记录晚饭30元")
        budget = WorkflowTask(id="budget", type="budget", goal="设置预算7500元")

        self.assertEqual(RoutePlan(mode="single", tasks=[bill]).mode, "single")
        self.assertEqual(RoutePlan(mode="multi", tasks=[bill, budget]).mode, "multi")
        self.assertEqual(RoutePlan(mode="open_planning").tasks, [])

    def test_route_plan_rejects_invalid_mode_task_counts(self):
        bill = WorkflowTask(id="bill", type="bill", goal="记录晚饭30元")
        with self.assertRaises(ValidationError):
            RoutePlan(mode="single", tasks=[])
        with self.assertRaises(ValidationError):
            RoutePlan(mode="multi", tasks=[bill])
        with self.assertRaises(ValidationError):
            RoutePlan(mode="open_planning", tasks=[bill])

    def test_build_route_plan_uses_one_top_level_model(self):
        expected = RoutePlan(
            mode="multi",
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
