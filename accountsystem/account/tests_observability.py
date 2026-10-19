"""OpenTelemetry P1 tests. All spans stay in memory; no collector or network is used."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

from django.test import SimpleTestCase
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from account.ai.gateway import agent as gateway
from account.ai.llm.failover import FailoverLLM
from account.ai.observability import telemetry
from account.ai.observability.telemetry import start_span
from account.ai.orchestrator import executor, unified_planner
from account.ai.orchestrator.state import new_state
from account.ai.orchestrator.task_schema import WorkflowPlan, WorkflowTask


class _StubModel:
    def __init__(self, name: str, *, result=None, exc: Exception | None = None):
        self.model_name = name
        self._result = result
        self._exc = exc

    def invoke(self, input, config=None, **kwargs):
        if self._exc is not None:
            raise self._exc
        return self._result

    def with_structured_output(self, schema, **kwargs):
        return self


class _UsageResult:
    usage_metadata = {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10}


class _Emitter:
    def __init__(self, publish=None):
        self.publish = publish
        self.finished = []

    def start_trace(self, **kwargs):
        return None

    def finish_trace(self, *args, **kwargs):
        self.finished.append((args, kwargs))


async def _drain_runtime(*args, **kwargs) -> list[dict]:
    return [item async for item in gateway.astream_accounting(*args, **kwargs)]


class TelemetryInitializationTests(SimpleTestCase):
    def tearDown(self):
        provider = telemetry._PROVIDER
        if provider is not None and hasattr(provider, "shutdown"):
            provider.shutdown()
        telemetry._reset_for_tests()

    def test_disabled_is_noop_and_business_still_runs(self):
        telemetry._reset_for_tests()
        model = _StubModel("stub", result="ok")
        with patch.dict(os.environ, {"OTEL_ENABLED": "false"}, clear=False):
            with patch.object(telemetry, "_build_otlp_exporter") as exporter:
                self.assertEqual(FailoverLLM([model]).invoke("metadata only"), "ok")
        exporter.assert_not_called()

    def test_enabled_initializes_and_exports_in_memory(self):
        telemetry._reset_for_tests()
        exporter = InMemorySpanExporter()
        with patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False):
            with patch.object(telemetry, "_build_otlp_exporter", return_value=exporter):
                self.assertTrue(telemetry.init_telemetry())
                with telemetry.start_span("agent.run"):
                    pass
                telemetry._PROVIDER.force_flush()
        self.assertEqual([span.name for span in exporter.get_finished_spans()], ["agent.run"])

    def test_exporter_initialization_failure_is_fail_open(self):
        telemetry._reset_for_tests()
        model = _StubModel("stub", result="ok")
        with patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False):
            with patch.object(
                telemetry,
                "_build_otlp_exporter",
                side_effect=RuntimeError("collector unavailable"),
            ):
                with self.assertLogs("account.ai.observability.telemetry", level="WARNING"):
                    self.assertFalse(telemetry.init_telemetry())
                self.assertEqual(FailoverLLM([model]).invoke("metadata only"), "ok")

    def test_span_close_failure_is_fail_open(self):
        class _BrokenManager:
            def __enter__(self):
                return telemetry._NOOP_SPAN

            def __exit__(self, *args):
                raise RuntimeError("export failed")

        class _BrokenTracer:
            def start_as_current_span(self, *args, **kwargs):
                return _BrokenManager()

        class _BrokenProvider:
            def get_tracer(self, *args, **kwargs):
                return _BrokenTracer()

        telemetry._set_tracer_provider_for_tests(_BrokenProvider())
        with self.assertLogs("account.ai.observability.telemetry", level="WARNING"):
            with telemetry.start_span("agent.run"):
                business_result = "ok"
        self.assertEqual(business_result, "ok")


class RuntimeSpanTests(SimpleTestCase):
    def setUp(self):
        self.exporter = InMemorySpanExporter()
        self.provider = TracerProvider(
            resource=Resource.create(
                {"service.name": "finpilot-agent-test", "deployment.environment": "test"}
            )
        )
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        telemetry._set_tracer_provider_for_tests(self.provider)

    def tearDown(self):
        self.provider.shutdown()
        telemetry._reset_for_tests()

    @staticmethod
    def _chat_plan() -> WorkflowPlan:
        return WorkflowPlan(
            tasks=[
                WorkflowTask(
                    id="chat_1",
                    type="chat",
                    action="respond",
                    goal="回答用户",
                    input={"message": "metadata only"},
                )
            ]
        )

    def test_runtime_tree_and_context_propagation(self):
        plan = self._chat_plan()
        planner_model = FailoverLLM([_StubModel("planner-model", result=plan)])
        task_model = FailoverLLM([_StubModel("task-model", result="ok")])
        captured_run_ids: list[str] = []

        def runner(user_input, user, **kwargs):
            task_model.invoke(["metadata only"])
            return {"success": True, "output": "ok", "intermediate_steps": []}

        def runtime(user_input, user, conversation_id, confirm, **kwargs):
            captured_run_ids.append(kwargs["run_id"])
            built = unified_planner.build_route_plan(user_input)
            state = new_state(user_input, user=user, run_id=kwargs["run_id"])
            executor.execute_plan(
                state,
                built,
                trace_id=kwargs["trace_id"],
                runtime_plan_id=kwargs["plan_id"],
            )
            return state["final_response"]

        with patch.object(gateway, "EventEmitter", _Emitter), patch.object(
            gateway, "run_orchestrator", side_effect=runtime
        ), patch.object(unified_planner, "planner_llm", planner_model), patch.object(
            executor, "_RUNNERS", {"chat": runner}
        ):
            asyncio.run(_drain_runtime("metadata only"))

        spans = list(self.exporter.get_finished_spans())
        by_name = {span.name: span for span in spans if span.name != "llm.invoke"}
        llm_spans = [span for span in spans if span.name == "llm.invoke"]
        root = by_name["agent.run"]
        planner = by_name["planner.build_plan"]
        plan_span = by_name["plan.execute"]
        task = by_name["task.execute"]

        self.assertEqual(len(llm_spans), 2)
        self.assertEqual(planner.parent.span_id, root.context.span_id)
        self.assertEqual(plan_span.parent.span_id, root.context.span_id)
        self.assertEqual(task.parent.span_id, plan_span.context.span_id)
        self.assertEqual(
            {span.parent.span_id for span in llm_spans},
            {planner.context.span_id, task.context.span_id},
        )
        self.assertEqual({span.context.trace_id for span in spans}, {root.context.trace_id})
        self.assertEqual(root.attributes["agent.run_id"], captured_run_ids[0])
        self.assertEqual(root.attributes["agent.logical_trace_id"], root.attributes["agent.plan_id"])
        self.assertEqual(planner.attributes["planner.task_count"], 1)
        self.assertEqual(plan_span.attributes["plan.status"], "completed")
        self.assertEqual(task.attributes["agent.domain"], "chat")
        self.assertEqual(task.attributes["agent.action"], "respond")

    def test_each_runtime_attempt_has_a_unique_run_id(self):
        run_ids: list[str] = []

        def runtime(*args, **kwargs):
            run_ids.append(kwargs["run_id"])
            return {"output": "", "plan_result": {"status": "success", "task_results": []}}

        with patch.object(gateway, "EventEmitter", _Emitter), patch.object(
            gateway, "run_orchestrator", side_effect=runtime
        ):
            asyncio.run(_drain_runtime("first"))
            asyncio.run(_drain_runtime("second"))

        self.assertEqual(len(run_ids), 2)
        self.assertNotEqual(run_ids[0], run_ids[1])

    def test_failover_is_one_logical_llm_span(self):
        llm = FailoverLLM(
            [
                _StubModel("primary", exc=RuntimeError("primary unavailable")),
                _StubModel("fallback", result=_UsageResult()),
            ]
        )
        with self.assertLogs("account.ai.llm.failover", level="WARNING"):
            llm.invoke(["metadata only"])

        spans = [span for span in self.exporter.get_finished_spans() if span.name == "llm.invoke"]
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.attributes["llm.model"], "fallback")
        self.assertEqual(span.attributes["llm.failover_count"], 1)
        self.assertEqual(span.attributes["llm.prompt_tokens"], 7)
        self.assertEqual(span.attributes["llm.completion_tokens"], 3)
        self.assertEqual(span.attributes["llm.total_tokens"], 10)
        self.assertEqual(
            [event.name for event in span.events if event.name == "llm.provider_failed"],
            ["llm.provider_failed"],
        )

    def test_unhandled_runtime_exception_marks_root_error(self):
        def runtime(*args, **kwargs):
            raise RuntimeError("runtime unavailable")

        with patch.object(gateway, "EventEmitter", _Emitter), patch.object(
            gateway, "run_orchestrator", side_effect=runtime
        ):
            asyncio.run(_drain_runtime("failure"))

        root = next(span for span in self.exporter.get_finished_spans() if span.name == "agent.run")
        self.assertEqual(root.attributes["agent.outcome"], "failed")
        self.assertEqual(root.status.status_code, StatusCode.ERROR)
        self.assertTrue(any(event.name == "exception" for event in root.events))

    def test_waiting_states_are_not_errors(self):
        def waiting_confirmation(*args, **kwargs):
            return {"output": "请确认", "confirm": {"need_confirm": True}}

        with patch.object(gateway, "EventEmitter", _Emitter), patch.object(
            gateway, "run_orchestrator", side_effect=waiting_confirmation
        ):
            asyncio.run(_drain_runtime("confirm"))

        root = next(span for span in self.exporter.get_finished_spans() if span.name == "agent.run")
        self.assertEqual(root.attributes["agent.outcome"], "waiting_confirmation")
        self.assertEqual(root.status.status_code, StatusCode.OK)

        self.exporter.clear()
        state = new_state("missing input")

        def waiting_input(*args, **kwargs):
            return {"output": "请补充信息", "needs_input": True, "intermediate_steps": []}

        with patch.object(executor, "_RUNNERS", {"chat": waiting_input}):
            with start_span("agent.run"):
                executor.execute_plan(state, self._chat_plan(), runtime_plan_id="plan-wait")

        spans = list(self.exporter.get_finished_spans())
        plan_span = next(span for span in spans if span.name == "plan.execute")
        task_span = next(span for span in spans if span.name == "task.execute")
        self.assertEqual(plan_span.attributes["plan.status"], "waiting_input")
        self.assertEqual(task_span.attributes["task.status"], "waiting_input")
        self.assertEqual(plan_span.status.status_code, StatusCode.OK)
        self.assertEqual(task_span.status.status_code, StatusCode.OK)

    def test_waiting_input_keeps_existing_agent_trace_partial_status(self):
        emitter = _Emitter()

        def waiting_input(*args, **kwargs):
            return {
                "output": "请补充信息",
                "plan_result": {
                    "status": "partial",
                    "task_results": [{"status": "waiting_input"}],
                },
            }

        with patch.object(gateway, "EventEmitter", return_value=emitter), patch.object(
            gateway, "run_orchestrator", side_effect=waiting_input
        ):
            asyncio.run(_drain_runtime("missing input"))

        root = next(span for span in self.exporter.get_finished_spans() if span.name == "agent.run")
        self.assertEqual(root.attributes["agent.outcome"], "waiting_input")
        self.assertEqual(root.status.status_code, StatusCode.OK)
        self.assertEqual(emitter.finished[-1][0][1], "partial")

    def test_real_exception_marks_llm_and_task_error(self):
        failed_model = FailoverLLM(
            [_StubModel("failed-model", exc=RuntimeError("provider unavailable"))]
        )

        def runner(*args, **kwargs):
            failed_model.invoke(["metadata only"])
            return {"success": True, "output": "unreachable"}

        state = new_state("failure")
        with patch.object(executor, "_RUNNERS", {"chat": runner}):
            with start_span("agent.run"):
                result = executor.execute_plan(
                    state,
                    self._chat_plan(),
                    runtime_plan_id="plan-failed",
                )

        spans = list(self.exporter.get_finished_spans())
        llm_span = next(span for span in spans if span.name == "llm.invoke")
        task_span = next(span for span in spans if span.name == "task.execute")
        plan_span = next(span for span in spans if span.name == "plan.execute")
        self.assertEqual(result["final_response"]["plan_result"]["status"], "failed")
        self.assertEqual(llm_span.status.status_code, StatusCode.ERROR)
        self.assertEqual(task_span.status.status_code, StatusCode.ERROR)
        self.assertTrue(any(event.name == "exception" for event in llm_span.events))
        self.assertTrue(any(event.name == "exception" for event in task_span.events))
        # Executor catches the task exception and returns a normal failure response.
        self.assertEqual(plan_span.status.status_code, StatusCode.OK)
