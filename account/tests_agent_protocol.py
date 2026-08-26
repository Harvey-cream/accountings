import json

from django.test import SimpleTestCase
from pydantic import ValidationError

from account.ai.orchestrator.protocol import (
    ConfirmationRequest,
    Plan,
    PlanStatus,
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
        self.assertEqual(restored.steps[-1].depends_on, ["create_bill", "update_budget"])

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
