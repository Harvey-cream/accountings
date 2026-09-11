from unittest.mock import patch

from django.test import TestCase

from account.ai.orchestrator.events import EventEmitter
from account.ai.orchestrator.executor import execute_plan
from account.ai.orchestrator.task_schema import WorkflowPlan, WorkflowTask
from account.models import AgentTrace, AgentTraceEvent


class AgentTraceRootTests(TestCase):
    def test_emitter_creates_root_and_finishes_with_duration(self):
        emitter = EventEmitter()
        emitter.start_trace(trace_id="trace-root", plan_id="plan-root", user_id=1)
        emitter.emit("plan.started", trace_id="trace-root", plan_id="plan-root")
        trace = emitter.finish_trace("trace-root", "completed")

        self.assertEqual(AgentTrace.objects.filter(trace_id="trace-root").count(), 1)
        self.assertEqual(AgentTraceEvent.objects.filter(trace_id="trace-root").count(), 1)
        self.assertEqual(trace.status, "completed")
        self.assertIsNotNone(trace.finished_at)
        self.assertIsNotNone(trace.duration_ms)

    def test_finish_trace_is_idempotent(self):
        emitter = EventEmitter()
        emitter.start_trace(trace_id="trace-idempotent")
        first = emitter.finish_trace("trace-idempotent", "completed")
        second = emitter.finish_trace("trace-idempotent", "failed")

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(second.status, "completed")

    def test_confirm_preview_does_not_emit_execution_events(self):
        emitter = EventEmitter()
        state = {"user_input": "晚饭30", "confirm": {}}
        plan = WorkflowPlan(
            tasks=[
                WorkflowTask(
                    id="bill",
                    type="bill",
                    action="create",
                    goal="记录晚饭30元",
                    input={"amount": 30, "description": "晚饭"},
                )
            ]
        )

        execute_plan(
            state,
            plan,
            trace_id="trace-preview",
            runtime_plan_id="plan-preview",
            event_emitter=emitter,
        )

        self.assertFalse(
            AgentTraceEvent.objects.filter(
                trace_id="trace-preview",
                event_type__in=["task.completed", "plan.completed"],
            ).exists()
        )

    def test_shared_trace_id_has_one_root_and_many_events(self):
        emitter = EventEmitter()
        emitter.start_trace(trace_id="trace-many", plan_id="plan-many")
        state = {"user_input": "早饭80，预算7900", "confirm": {"confirmed_plan": True}}
        plan = WorkflowPlan(
            tasks=[
                WorkflowTask(id="bill", type="bill", action="create", goal="记录早饭80元", input={"amount": 80}),
                WorkflowTask(id="budget", type="budget", action="set_budget", goal="设置预算7900元", input={"amount": 7900, "period": "2026-09", "budget_type": "month"}),
            ]
        )

        with patch(
            "account.ai.orchestrator.executor._execute_task",
            return_value={"output": "处理完成", "intermediate_steps": []},
        ):
            execute_plan(
                state,
                plan,
                trace_id="trace-many",
                runtime_plan_id="plan-many",
                event_emitter=emitter,
            )
        emitter.finish_trace("trace-many", "completed")

        self.assertEqual(AgentTrace.objects.filter(trace_id="trace-many").count(), 1)
        self.assertGreater(AgentTraceEvent.objects.filter(trace_id="trace-many").count(), 1)
