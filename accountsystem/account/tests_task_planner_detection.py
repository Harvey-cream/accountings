from unittest.mock import patch

from django.test import SimpleTestCase

from account.ai.orchestrator.task_planner import MultiTaskDecision, is_probably_multi


class TaskPlannerDetectionTests(SimpleTestCase):
    def test_keyword_multi_request_short_circuits_without_llm(self):
        with patch("account.ai.orchestrator.task_planner.get_llm") as mock_get_llm:
            self.assertTrue(is_probably_multi("记一笔午饭20，再把预算设置为7500"))
        mock_get_llm.assert_not_called()

    def test_semantic_multi_request_uses_simple_detector(self):
        detector = patch("account.ai.orchestrator.task_planner.get_llm")
        with detector as mock_get_llm:
            mock_model = mock_get_llm.return_value
            mock_detector = mock_model.with_structured_output.return_value
            mock_detector.invoke.return_value = MultiTaskDecision(
                domains=["bill", "budget"],
                is_multi=True,
                reason="semantic_multi",
            )

            self.assertTrue(is_probably_multi("早饭20，晚饭30预算设置为7500"))
            mock_get_llm.assert_called_once_with("simple")

    def test_single_domain_request_stays_single(self):
        detector = patch("account.ai.orchestrator.task_planner.get_llm")
        with detector as mock_get_llm:
            mock_model = mock_get_llm.return_value
            mock_detector = mock_model.with_structured_output.return_value
            mock_detector.invoke.return_value = MultiTaskDecision(
                domains=["budget"],
                is_multi=False,
                reason="single_budget",
            )

            self.assertFalse(is_probably_multi("预算设置为7500"))
