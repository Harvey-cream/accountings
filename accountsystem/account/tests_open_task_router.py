from unittest.mock import patch

from django.test import SimpleTestCase

from account.ai.orchestrator.open_task_router import TaskRoute, is_open_planning


class OpenTaskRouterTests(SimpleTestCase):
    def test_open_task_router_uses_simple_model_directly(self):
        with patch("account.ai.orchestrator.open_task_router.get_llm") as mock_get_llm:
            mock_model = mock_get_llm.return_value
            mock_router = mock_model.with_structured_output.return_value
            mock_router.invoke.return_value = TaskRoute(
                task_type="open_planning",
                reason="analysis_request",
            )

            self.assertTrue(is_open_planning("帮我分析一下最近三个月的消费趋势"))
            mock_get_llm.assert_called_once_with("simple")

    def test_open_task_router_can_reject_long_but_fixed_request(self):
        with patch("account.ai.orchestrator.open_task_router.get_llm") as mock_get_llm:
            mock_model = mock_get_llm.return_value
            mock_router = mock_model.with_structured_output.return_value
            mock_router.invoke.return_value = TaskRoute(
                task_type="bill",
                reason="fixed_business_combo",
            )

            self.assertFalse(is_open_planning("早饭20，晚饭30预算设置为7500"))
