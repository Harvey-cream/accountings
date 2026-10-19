"""OpenTelemetry P2 boundary tests using only an in-memory exporter."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

from django.test import SimpleTestCase
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from account.ai.agents.supervisor.asset import asset_agent
from account.ai.agents.supervisor.bill import bill_agent
from account.ai.agents.supervisor.budget import budget_agent
from account.ai.agents.supervisor.chat import chat_agent
from account.ai.agents.supervisor.invoice import invoice_agent
from account.ai.knowledge.retriever import finance_retriever
from account.ai.knowledge.tools import build_knowledge_tools
from account.ai.llm.failover import FailoverLLM
from account.ai.observability import telemetry
from account.ai.observability.context import WorkflowContext, use_workflow_context
from account.ai.observability.telemetry import start_span
from account.ai.observability.tools import instrument_tool
from account.ai.orchestrator import executor
from account.ai.orchestrator.state import new_state
from account.ai.orchestrator.task_schema import WorkflowPlan, WorkflowTask
from account.ai.tools.finance_tools import build_bill_tools
from account.ai.tools.tool_policy import allowed_tool_names
from account.services import expense_service
from account.services.errors import ServiceError


class _Chain:
    def __init__(self, callback):
        self.callback = callback

    def invoke(self, payload, config=None):
        return self.callback(payload)


class _Retriever:
    def __init__(self, *, result=None, exc: Exception | None = None):
        self.result = [] if result is None else result
        self.exc = exc

    def retrieve(self, query):
        if self.exc is not None:
            raise self.exc
        return self.result


class _Index:
    def __init__(self, retriever):
        self.retriever = retriever

    def as_retriever(self, *, similarity_top_k):
        return self.retriever


class _Model:
    model_name = "p2-test-model"

    def invoke(self, input, config=None, **kwargs):
        return "ok"


class RuntimeP2SpanTests(SimpleTestCase):
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

    def _spans(self, name: str):
        return [span for span in self.exporter.get_finished_spans() if span.name == name]

    def _one(self, name: str):
        spans = self._spans(name)
        self.assertEqual(len(spans), 1, f"expected one {name}, got {len(spans)}")
        return spans[0]

    @staticmethod
    def _bill_query_plan():
        return WorkflowPlan(
            tasks=[
                WorkflowTask(
                    id="bill_query_1",
                    type="bill",
                    action="query",
                    goal="查询账单",
                    input={},
                )
            ]
        )

    def test_bill_query_real_tree_and_direct_invoke_have_one_tool_span(self):
        def run_chain(payload):
            tool = next(tool for tool in build_bill_tools(None) if tool.name == "query_bills")
            tool.invoke({})
            return {"success": True, "output": "ok", "intermediate_steps": []}

        state = new_state("metadata only")
        with patch.object(bill_agent, "_build_chain", return_value=_Chain(run_chain)), patch.object(
            executor, "_RUNNERS", {"bill": bill_agent.run}
        ), patch.object(expense_service, "query_expense", return_value=[]):
            with start_span("agent.run"):
                executor.execute_plan(
                    state,
                    self._bill_query_plan(),
                    runtime_plan_id="plan-p2-bill",
                )

        task = self._one("task.execute")
        workflow = self._one("workflow.run")
        tool = self._one("tool.execute")
        service = self._one("service.call")
        root = self._one("agent.run")

        self.assertEqual(workflow.parent.span_id, task.context.span_id)
        self.assertEqual(tool.parent.span_id, workflow.context.span_id)
        self.assertEqual(service.parent.span_id, tool.context.span_id)
        self.assertEqual(
            {span.context.trace_id for span in (root, task, workflow, tool, service)},
            {root.context.trace_id},
        )
        self.assertEqual(workflow.attributes["agent.domain"], "bill")
        self.assertEqual(workflow.attributes["agent.action"], "query")
        self.assertEqual(workflow.attributes["agent.task_id"], "bill_query_1")
        self.assertEqual(workflow.attributes["workflow.status"], "completed")
        self.assertTrue(tool.attributes["tool.read_only"])
        self.assertFalse(tool.attributes["tool.confirmed"])
        self.assertEqual(service.attributes["service.name"], "expense_service")

    def test_tool_node_executes_in_workflow_trace_without_duplicate_span(self):
        context = WorkflowContext("bill", "query", "bill_tool_node", False)
        with patch.object(expense_service, "query_expense", return_value=[]):
            with start_span("workflow.run") as workflow_span:
                with use_workflow_context(context):
                    tool = next(
                        tool for tool in build_bill_tools(None) if tool.name == "query_bills"
                    )
                    node = ToolNode([tool])
                    node.invoke(
                        {
                            "messages": [
                                AIMessage(
                                    content="",
                                    tool_calls=[
                                        {
                                            "name": "query_bills",
                                            "args": {},
                                            "id": "call-p2-1",
                                            "type": "tool_call",
                                        }
                                    ],
                                )
                            ]
                        }
                    )

        tool_span = self._one("tool.execute")
        service_span = self._one("service.call")
        self.assertEqual(tool_span.parent.span_id, workflow_span.context.span_id)
        self.assertEqual(service_span.parent.span_id, tool_span.context.span_id)

    def test_existing_llm_span_is_a_workflow_child(self):
        model = FailoverLLM([_Model()])

        def run_chain(payload):
            model.invoke(["metadata only"])
            return {"output": "ok", "intermediate_steps": []}

        with patch.object(bill_agent, "_build_chain", return_value=_Chain(run_chain)):
            bill_agent.run("metadata only", task_action="query", task_id="bill-llm-1")

        workflow = self._one("workflow.run")
        llm = self._one("llm.invoke")
        self.assertEqual(llm.parent.span_id, workflow.context.span_id)
        self.assertEqual(llm.context.trace_id, workflow.context.trace_id)

    def test_instrument_tool_is_idempotent(self):
        context = WorkflowContext("bill", "query", "bill_duplicate", False)
        with patch.object(expense_service, "query_expense", return_value=[]):
            with start_span("workflow.run"):
                with use_workflow_context(context):
                    tool = next(
                        tool for tool in build_bill_tools(None) if tool.name == "query_bills"
                    )
                    instrument_tool(tool, domain="bill", service_name="expense_service")
                    tool.invoke({})

        self._one("tool.execute")
        self._one("service.call")

    def test_confirmed_mutation_attributes_and_policy_are_preserved(self):
        self.assertNotIn("create_bill", allowed_tool_names("bill", "create", False))
        self.assertIn("create_bill", allowed_tool_names("bill", "create", True))

        context = WorkflowContext("bill", "create", "bill_create_1", True)
        with patch.object(expense_service, "create_expense", return_value={"id": 1}):
            with start_span("workflow.run"):
                with use_workflow_context(context):
                    tool = next(
                        tool for tool in build_bill_tools(None) if tool.name == "create_bill"
                    )
                    result = json.loads(tool.invoke({"amount": 12.5}))

        span = self._one("tool.execute")
        self.assertTrue(result["success"])
        self.assertFalse(span.attributes["tool.read_only"])
        self.assertTrue(span.attributes["tool.confirmed"])
        self.assertEqual(span.attributes["tool.operation"], "create")

    def test_service_technical_exception_is_error_without_changing_tool_result(self):
        context = WorkflowContext("bill", "query", "bill_service_error", False)
        with patch.object(
            expense_service, "query_expense", side_effect=RuntimeError("database unavailable")
        ):
            with start_span("workflow.run"):
                with use_workflow_context(context):
                    tool = next(
                        tool for tool in build_bill_tools(None) if tool.name == "query_bills"
                    )
                    result = json.loads(tool.invoke({}))

        service = self._one("service.call")
        tool_span = self._one("tool.execute")
        self.assertFalse(result["success"])
        self.assertEqual(service.attributes["service.status"], "failed")
        self.assertEqual(service.status.status_code, StatusCode.ERROR)
        self.assertTrue(any(event.name == "exception" for event in service.events))
        # run_service has always converted technical failures into a Tool JSON result.
        self.assertEqual(tool_span.attributes["tool.status"], "failed")
        self.assertEqual(tool_span.status.status_code, StatusCode.OK)

    def test_service_business_error_remains_a_normal_span_outcome(self):
        context = WorkflowContext("bill", "query", "bill_service_business", False)
        with patch.object(
            expense_service, "query_expense", side_effect=ServiceError("not found")
        ):
            with start_span("workflow.run"):
                with use_workflow_context(context):
                    tool = next(
                        tool for tool in build_bill_tools(None) if tool.name == "query_bills"
                    )
                    result = json.loads(tool.invoke({}))

        service = self._one("service.call")
        self.assertFalse(result["success"])
        self.assertEqual(service.attributes["service.status"], "business_error")
        self.assertEqual(service.status.status_code, StatusCode.OK)
        self.assertFalse(any(event.name == "exception" for event in service.events))

    def test_rag_zero_results_tree_is_ok_and_contains_no_query_attribute(self):
        private_query = "PRIVATE-RAG-QUERY-DO-NOT-EXPORT"
        context = WorkflowContext("chat", "respond", "chat_rag_1", False)
        with patch.object(
            finance_retriever, "_get_index", return_value=_Index(_Retriever(result=[]))
        ):
            with start_span("workflow.run"):
                with use_workflow_context(context):
                    tool = build_knowledge_tools(domain="chat")[0]
                    result = json.loads(tool.invoke({"query": private_query, "top_k": 3}))

        tool_span = self._one("tool.execute")
        rag = self._one("rag.retrieve")
        self.assertEqual(rag.parent.span_id, tool_span.context.span_id)
        self.assertEqual(rag.context.trace_id, tool_span.context.trace_id)
        self.assertEqual(rag.attributes["rag.top_k"], 3)
        self.assertEqual(rag.attributes["rag.result_count"], 0)
        self.assertEqual(rag.status.status_code, StatusCode.OK)
        self.assertTrue(result["success"])
        self.assertNotIn("query", rag.attributes)
        self.assertNotIn(private_query, repr(dict(rag.attributes)))

    def test_rag_technical_exception_is_error_but_keeps_existing_empty_result(self):
        context = WorkflowContext("chat", "respond", "chat_rag_error", False)
        with patch.object(
            finance_retriever,
            "_get_index",
            return_value=_Index(_Retriever(exc=RuntimeError("vector store unavailable"))),
        ), patch.object(finance_retriever, "log_agent_exc"):
            with start_span("workflow.run"):
                with use_workflow_context(context):
                    tool = build_knowledge_tools(domain="chat")[0]
                    result = json.loads(tool.invoke({"query": "metadata only"}))

        rag = self._one("rag.retrieve")
        tool_span = self._one("tool.execute")
        self.assertEqual(rag.status.status_code, StatusCode.ERROR)
        self.assertTrue(any(event.name == "exception" for event in rag.events))
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], [])
        self.assertEqual(tool_span.status.status_code, StatusCode.OK)

    def test_chat_rag_real_workflow_entry_has_task_to_rag_tree(self):
        def run_chain(payload):
            build_knowledge_tools(domain="chat")[0].invoke(
                {"query": "metadata only", "top_k": 2}
            )
            return {"output": "ok", "intermediate_steps": []}

        plan = WorkflowPlan(
            tasks=[
                WorkflowTask(
                    id="chat_rag_task",
                    type="chat",
                    action="respond",
                    goal="回答问题",
                    input={"message": "metadata only"},
                )
            ]
        )
        state = new_state("metadata only")
        with patch.object(chat_agent, "_build_chain", return_value=_Chain(run_chain)), patch.object(
            executor, "_RUNNERS", {"chat": chat_agent.run}
        ), patch.object(
            finance_retriever, "_get_index", return_value=_Index(_Retriever(result=[]))
        ):
            with start_span("agent.run"):
                executor.execute_plan(state, plan, runtime_plan_id="plan-p2-rag")

        task = self._one("task.execute")
        workflow = self._one("workflow.run")
        tool = self._one("tool.execute")
        rag = self._one("rag.retrieve")
        self.assertEqual(workflow.parent.span_id, task.context.span_id)
        self.assertEqual(tool.parent.span_id, workflow.context.span_id)
        self.assertEqual(rag.parent.span_id, tool.context.span_id)

    def test_all_five_domain_run_entries_create_one_workflow_span(self):
        cases = (
            (bill_agent, "bill", "query"),
            (budget_agent, "budget", "query_budget"),
            (asset_agent, "asset", "query"),
            (invoice_agent, "invoice", "query"),
            (chat_agent, "chat", "respond"),
        )
        for module, domain, action in cases:
            with self.subTest(domain=domain):
                self.exporter.clear()
                with patch.object(
                    module,
                    "_build_chain",
                    return_value=_Chain(
                        lambda payload: {"output": "ok", "intermediate_steps": []}
                    ),
                ):
                    with start_span("task.execute") as task_span:
                        module.run(
                            "metadata only",
                            task_action=action,
                            task_id=f"{domain}_task",
                        )
                workflow = self._one("workflow.run")
                self.assertEqual(workflow.parent.span_id, task_span.context.span_id)
                self.assertEqual(workflow.attributes["agent.domain"], domain)
                self.assertEqual(workflow.attributes["agent.action"], action)
                self.assertEqual(workflow.attributes["workflow.name"], domain)

    def test_waiting_workflow_is_ok_and_real_exception_is_error(self):
        with patch.object(
            bill_agent,
            "_build_chain",
            return_value=_Chain(
                lambda payload: {
                    "output": "need input",
                    "needs_input": True,
                    "intermediate_steps": [],
                }
            ),
        ):
            bill_agent.run("metadata only", task_action="create", task_id="wait-1")

        waiting = self._one("workflow.run")
        self.assertEqual(waiting.attributes["workflow.status"], "waiting_input")
        self.assertEqual(waiting.status.status_code, StatusCode.OK)

        self.exporter.clear()

        def fail(payload):
            raise RuntimeError("workflow unavailable")

        with patch.object(bill_agent, "_build_chain", return_value=_Chain(fail)):
            with self.assertRaisesRegex(RuntimeError, "workflow unavailable"):
                bill_agent.run("metadata only", task_action="query", task_id="failed-1")

        failed = self._one("workflow.run")
        self.assertEqual(failed.attributes["workflow.status"], "failed")
        self.assertEqual(failed.status.status_code, StatusCode.ERROR)
        self.assertTrue(any(event.name == "exception" for event in failed.events))


class RuntimeP2DisabledTests(SimpleTestCase):
    def tearDown(self):
        provider = telemetry._PROVIDER
        if provider is not None and hasattr(provider, "shutdown"):
            provider.shutdown()
        telemetry._reset_for_tests()

    def test_disabled_keeps_workflow_tool_service_and_rag_behavior(self):
        telemetry._reset_for_tests()

        def run_chain(payload):
            tool = next(tool for tool in build_bill_tools(None) if tool.name == "query_bills")
            return {
                "output": tool.invoke({}),
                "intermediate_steps": [],
            }

        with patch.dict(os.environ, {"OTEL_ENABLED": "false"}, clear=False), patch.object(
            telemetry, "_build_otlp_exporter"
        ) as exporter, patch.object(
            bill_agent, "_build_chain", return_value=_Chain(run_chain)
        ), patch.object(
            expense_service, "query_expense", return_value=[]
        ), patch.object(
            finance_retriever, "_get_index", return_value=_Index(_Retriever(result=[]))
        ):
            workflow_result = bill_agent.run(
                "metadata only", task_action="query", task_id="disabled-1"
            )
            rag_result = finance_retriever.retrieve_finance_knowledge("metadata only")

        exporter.assert_not_called()
        self.assertTrue(json.loads(workflow_result["output"])["success"])
        self.assertEqual(rag_result, [])
