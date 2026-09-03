from django.test import SimpleTestCase

from account.ai.agents.supervisor.asset.asset_agent import _to_graph_input as asset_input
from account.ai.agents.supervisor.invoice.invoice_agent import _to_graph_input as invoice_input
from account.ai.orchestrator.executor import _build_plan_confirmation
from account.ai.orchestrator.task_schema import WorkflowTask


class PlanAssetInvoiceTests(SimpleTestCase):
    def test_plan_confirmation_supports_asset_and_invoice_mutations(self):
        confirmations = _build_plan_confirmation([
            WorkflowTask(
                id="asset_update",
                type="asset",
                goal="调整账户余额",
                input={"action": "adjust_balance", "target_id": 7, "delta": 100},
            ),
            WorkflowTask(
                id="invoice_update",
                type="invoice",
                goal="修改发票抬头",
                input={"action": "update", "target_id": 9, "name": "新公司"},
            ),
        ])

        self.assertEqual(
            [(item["entity"], item["action"], item["task_id"]) for item in confirmations["confirmations"]],
            [("asset", "adjust_balance", "asset_update"), ("invoice", "update", "invoice_update")],
        )

    def test_plan_confirmation_skips_asset_and_invoice_queries(self):
        self.assertIsNone(
            _build_plan_confirmation([
                WorkflowTask(id="asset_query", type="asset", goal="查询净资产"),
                WorkflowTask(id="invoice_query", type="invoice", goal="查询发票"),
            ])
        )

    def test_asset_task_input_maps_to_workflow_state(self):
        state = asset_input({
            "input": "调整支付宝余额",
            "history": [],
            "user": None,
            "task_input": {"action": "adjust_balance", "target_id": 7},
            "confirm": {},
        })

        self.assertEqual(state["intent"], "adjust_balance")
        self.assertEqual(state["target_account"], {"id": 7})

    def test_invoice_task_input_maps_to_workflow_state(self):
        state = invoice_input({
            "input": "修改发票抬头",
            "history": [],
            "user": None,
            "task_input": {"action": "update", "target_id": 9},
            "confirm": {},
        })

        self.assertEqual(state["intent"], "update")
        self.assertEqual(state["target_invoice"], {"id": 9})
