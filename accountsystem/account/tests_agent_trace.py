from unittest.mock import patch

from django.test import SimpleTestCase

from account.ai.orchestrator.executor import execute_plan
from account.ai.orchestrator.task_schema import WorkflowPlan, WorkflowTask


class _EventCollector:
    def __init__(self):
        self.events = []

    def emit(self, event_type, **kwargs):
        self.events.append({"event_type": event_type, **kwargs})


class AgentTraceLifecycleTests(SimpleTestCase):
    def _plan(self, *tasks):
        return WorkflowPlan(tasks=list(tasks))

    def test_single_bill_emits_plan_task_and_agent_events_in_order(self):
        collector = _EventCollector()
        state = {"user_input": "晚饭30", "confirm": {"confirmed_plan": True}}
        plan = self._plan(WorkflowTask(id="bill", type="bill", action="create", goal="记录晚饭30元", input={"amount": 30}))

        with patch(
            "account.ai.orchestrator.executor._execute_task",
            return_value={"output": "账单完成", "intermediate_steps": []},
        ):
            execute_plan(
                state,
                plan,
                trace_id="trace-1",
                runtime_plan_id="plan-1",
                event_emitter=collector,
            )

        self.assertEqual(
            [event["event_type"] for event in collector.events],
            [
                "plan.started",
                "task.started",
                "agent.started",
                "agent.completed",
                "task.completed",
                "plan.completed",
            ],
        )
        self.assertTrue(all(event["trace_id"] == "trace-1" for event in collector.events))
        self.assertEqual(collector.events[1]["task_id"], "bill")
        self.assertEqual(collector.events[2]["agent"], "bill")

    def test_bill_budget_events_follow_plan_order(self):
        collector = _EventCollector()
        state = {"user_input": "早饭80，预算7900", "confirm": {"confirmed_plan": True}}
        plan = self._plan(
            WorkflowTask(id="bill", type="bill", action="create", goal="记录早饭80元", input={"amount": 80}),
            WorkflowTask(id="budget", type="budget", action="set_budget", goal="设置预算7900元", input={"amount": 7900, "period": "2026-09", "budget_type": "month"}),
        )

        with patch(
            "account.ai.orchestrator.executor._execute_task",
            return_value={"output": "处理完成", "intermediate_steps": []},
        ):
            execute_plan(
                state,
                plan,
                trace_id="trace-2",
                runtime_plan_id="plan-2",
                event_emitter=collector,
            )

        self.assertEqual(
            [(event["event_type"], event["task_id"]) for event in collector.events],
            [
                ("plan.started", ""),
                ("task.started", "bill"),
                ("agent.started", "bill"),
                ("agent.completed", "bill"),
                ("task.completed", "bill"),
                ("task.started", "budget"),
                ("agent.started", "budget"),
                ("agent.completed", "budget"),
                ("task.completed", "budget"),
                ("plan.completed", ""),
            ],
        )

    def test_agent_exception_emits_failure_chain(self):
        collector = _EventCollector()
        state = {"user_input": "晚饭30", "confirm": {"confirmed_plan": True}}
        plan = self._plan(WorkflowTask(id="bill", type="bill", action="create", goal="记录晚饭30元", input={"amount": 30}))

        with patch(
            "account.ai.orchestrator.executor._execute_task",
            side_effect=RuntimeError("workflow failed"),
        ):
            with self.assertRaises(RuntimeError):
                execute_plan(
                    state,
                    plan,
                    trace_id="trace-3",
                    runtime_plan_id="plan-3",
                    event_emitter=collector,
                )

        self.assertEqual(
            [event["event_type"] for event in collector.events],
            [
                "plan.started",
                "task.started",
                "agent.started",
                "agent.failed",
                "task.failed",
                "plan.failed",
            ],
        )
