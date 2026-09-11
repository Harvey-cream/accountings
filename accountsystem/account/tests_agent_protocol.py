import json

from django.test import SimpleTestCase
from pydantic import ValidationError

from account.ai.llm.response import to_api_dict
from account.ai.orchestrator.protocol import (
    ConfirmationRequest,
    Plan,
    PlanStep,
    StepContext,
    StepError,
    StepResult,
    StepStatus,
    StepType,
)


class AgentProtocolTests(SimpleTestCase):
    def test_plan_supports_business_steps_followed_by_open_planning(self):
        plan = Plan(
            plan_id="plan-1",
            original_request="今天消费200，预算改为7000并规划资金使用",
            steps=[
                PlanStep(
                    step_id="create_bill",
                    step_type=StepType.BILL,
                    action="create",
                    goal="记录今天200元支出",
                ),
                PlanStep(
                    step_id="update_budget",
                    step_type=StepType.BUDGET,
                    action="update",
                    goal="将本月预算改为7000元",
                    depends_on=["create_bill"],
                ),
                PlanStep(
                    step_id="plan_funds",
                    step_type=StepType.OPEN_PLANNING,
                    action="analyze",
                    goal="分析接下来的资金使用规划",
                    depends_on=["create_bill", "update_budget"],
                ),
            ],
        )

        payload = plan.model_dump(mode="json")
        restored = Plan.model_validate(json.loads(json.dumps(payload)))

        self.assertEqual(restored, plan)
        self.assertEqual(restored.steps[-1].step_type, StepType.OPEN_PLANNING)

    def test_plan_rejects_duplicate_or_unknown_dependencies(self):
        with self.assertRaises(ValidationError):
            Plan(
                plan_id="plan-1",
                steps=[
                    PlanStep(
                        step_id="bill",
                        step_type=StepType.BILL,
                        action="create",
                        depends_on=["bill"],
                    )
                ],
            )

        with self.assertRaises(ValidationError):
            Plan(
                plan_id="plan-1",
                steps=[
                    PlanStep(
                        step_id="bill",
                        step_type=StepType.BILL,
                        action="create",
                    ),
                    PlanStep(
                        step_id="budget",
                        step_type=StepType.BUDGET,
                        action="update",
                        depends_on=["missing"],
                    ),
                ],
            )

        with self.assertRaises(ValidationError):
            Plan(
                plan_id="plan-1",
                steps=[
                    PlanStep(
                        step_id="bill",
                        step_type=StepType.BILL,
                        action="create",
                    ),
                    PlanStep(
                        step_id="bill",
                        step_type=StepType.BUDGET,
                        action="update",
                    ),
                ],
            )

    def test_step_context_and_result_keep_structured_data(self):
        bill_result = StepResult(
            plan_id="plan-1",
            step_id="create_bill",
            step_type=StepType.BILL,
            action="create",
            status=StepStatus.COMPLETED,
            success=True,
            data={"record_id": 42, "amount": "200.00"},
            entity_ids=[42],
            message="账单已创建",
        )
        context = StepContext(
            plan_id="plan-1",
            step_id="update_budget",
            step_type=StepType.BUDGET,
            input={"amount": "7000.00", "period": "2026-08"},
            planning_request="分析接下来的资金使用规划",
            completed_results={"create_bill": bill_result},
        )

        payload = context.model_dump(mode="json")

        self.assertEqual(payload["completed_results"]["create_bill"]["data"]["record_id"], 42)
        self.assertEqual(payload["input"]["amount"], "7000.00")

    def test_step_result_supports_failure_and_confirmation_states(self):
        failed = StepResult(
            plan_id="plan-1",
            step_id="update_budget",
            step_type=StepType.BUDGET,
            action="update",
            status=StepStatus.FAILED,
            success=False,
            error=StepError(code="budget_update_failed", message="预算更新失败"),
        )
        waiting = StepResult(
            plan_id="plan-1",
            step_id="create_bill",
            step_type=StepType.BILL,
            action="create",
            status=StepStatus.WAITING_CONFIRMATION,
            success=False,
            confirmation=ConfirmationRequest(
                prompt="是否确认记录这笔账单？",
                token="confirm-1",
                payload={"amount": "200.00"},
            ),
        )

        self.assertEqual(failed.error.code, "budget_update_failed")
        self.assertEqual(waiting.confirmation.token, "confirm-1")

        with self.assertRaises(ValidationError):
            StepResult(
                plan_id="plan-1",
                step_id="create_bill",
                step_type=StepType.BILL,
                action="create",
                status=StepStatus.WAITING_CONFIRMATION,
                success=False,
            )

    def test_to_api_dict_returns_transaction_and_budget_cards(self):
        result = to_api_dict(
            {
                "output": "已完成记账和预算设置",
                "intermediate_steps": [
                    (
                        {"name": "create_bill"},
                        json.dumps(
                            {
                                "success": True,
                                "data": {
                                    "id": 1,
                                    "type": "expense",
                                    "category": "餐饮",
                                    "amount": 20,
                                    "remark": "早饭",
                                    "icon": "food-o",
                                },
                            },
                            ensure_ascii=False,
                        ),
                    ),
                    (
                        {"name": "create_budget"},
                        json.dumps(
                            {
                                "success": True,
                                "data": {
                                    "id": 2,
                                    "amount": 7500,
                                    "budget_type": "month",
                                    "period": "2026-08",
                                    "is_total": True,
                                    "category": None,
                                },
                                "message": "预算已保存",
                            },
                            ensure_ascii=False,
                        ),
                    ),
                ],
            }
        )

    def test_workflow_result_preserves_analysis_view_in_step_and_plan(self):
        from account.ai.orchestrator.result_adapter import adapt_workflow_result
        from account.ai.orchestrator.result_aggregator import aggregate_plan_results

        view = {
            "summary": {"text": "本月餐饮偏高"},
            "sections": [{"title": "消费分析", "items": [{"text": "餐饮占比过高"}]}],
        }
        step = adapt_workflow_result(
            {
                "output": "本月餐饮偏高",
                "analysis_view": view,
                "crew_result": {"summary": "本月餐饮偏高"},
            },
            plan_id="plan-1",
            step_id="plan_funds",
            step_type=StepType.OPEN_PLANNING,
            action="analyze",
        )
        plan = aggregate_plan_results([step], plan_id="plan-1")

        self.assertEqual(step.data["analysis_view"], view)
        self.assertEqual(plan.analysis_view, view)
        self.assertEqual(to_api_dict({"plan_result": plan.model_dump(mode="json")})["analysis_view"], view)

    def test_result_protocol_covers_bill_and_budget(self):
        from account.ai.orchestrator.result_aggregator import aggregate_plan_results

        result = aggregate_plan_results([
            StepResult(
                plan_id="plan-1",
                step_id="bill",
                step_type=StepType.BILL,
                action="execute",
                status=StepStatus.COMPLETED,
                success=True,
                message="已记录早饭20元、晚饭30元，共50元",
                summary="已记录早饭20元、晚饭30元，共50元",
            ),
            StepResult(
                plan_id="plan-1",
                step_id="budget",
                step_type=StepType.BUDGET,
                action="execute",
                status=StepStatus.COMPLETED,
                success=True,
                data={"amount": 7500},
                message="本月总预算已设置为7500元",
                summary="本月总预算已设置为7500元",
            ),
        ], plan_id="plan-1")

        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.task_results), 2)
        self.assertIn("7500", result.summary)
