import json

from django.test import SimpleTestCase
from pydantic import BaseModel

from account.ai.orchestrator.protocol import StepStatus, StepType
from account.ai.orchestrator.result_adapter import _json_safe, adapt_workflow_result
from account.ai.orchestrator.result_aggregator import aggregate_plan_results


class _Payload(BaseModel):
    name: str
    amount: int


class _ToolCall:
    def __repr__(self):
        return "<tool-call>"


class ResultProtocolTests(SimpleTestCase):
    def _result(self, step_id, step_type, output, **extra):
        return adapt_workflow_result(
            {"output": output, "intermediate_steps": [], **extra},
            plan_id="plan-1",
            step_id=step_id,
            step_type=step_type,
            action=extra.pop("action", "query"),
        )

    def test_bill_and_budget_results_are_both_aggregated(self):
        result = aggregate_plan_results([
            self._result("meals", StepType.BILL, "已记录早饭20元、晚饭30元，共50元"),
            self._result("budget", StepType.BUDGET, "本月总预算已设置为7500元"),
        ], plan_id="plan-1")

        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.task_results), 2)
        self.assertIn("7500", result.summary)

    def test_success_and_failure_are_partial(self):
        result = aggregate_plan_results([
            self._result("bill", StepType.BILL, "记账完成"),
            self._result("budget", StepType.BUDGET, "预算失败", error={"code": "failed", "message": "预算失败"}),
        ])
        self.assertEqual(result.status, "partial")

    def test_confirmation_becomes_waiting_confirmation(self):
        result = self._result(
            "bill",
            StepType.BILL,
            "请确认",
            confirm={"need_confirm": True, "entity": "bill", "action": "batch_create"},
        )
        self.assertEqual(result.status, StepStatus.WAITING_CONFIRMATION)
        self.assertIsNotNone(result.confirmation)

    def test_json_safe_normalizes_legacy_intermediate_steps(self):
        raw = ({"name": "create_budget"}, "预算已保存")
        normalized = _json_safe([raw, {"payload": _Payload(name="budget", amount=7500)}, _ToolCall()])

        self.assertEqual(normalized[0], [{"name": "create_budget"}, "预算已保存"])
        self.assertEqual(normalized[1]["payload"], {"name": "budget", "amount": 7500})
        self.assertEqual(normalized[2], "<tool-call>")

    def test_budget_tool_tuple_can_build_step_result(self):
        result = self._result(
            "budget",
            StepType.BUDGET,
            "预算已保存",
            data={"amount": 7500},
            intermediate_steps=[({"name": "create_budget"}, "预算已保存")],
        )

        self.assertEqual(result.status, StepStatus.COMPLETED)
        self.assertEqual(result.data["amount"], 7500)
        self.assertEqual(result.intermediate_steps[0], [{"name": "create_budget"}, "预算已保存"])
