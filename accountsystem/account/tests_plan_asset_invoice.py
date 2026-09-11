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
                action="adjust_balance",
                input={"account_id": 7, "delta": 100},
            ),
            WorkflowTask(
                id="invoice_update",
                type="invoice",
                goal="修改发票抬头",
                action="update",
                input={"invoice_id": 9, "name": "新公司", "tax_id": "税号"},
            ),
        ])

        self.assertEqual(
            [(item["entity"], item["action"], item["task_id"]) for item in confirmations["confirmations"]],
            [("asset", "adjust_balance", "asset_update"), ("invoice", "update", "invoice_update")],
        )

    def test_plan_confirmation_skips_asset_and_invoice_queries(self):
        self.assertIsNone(
            _build_plan_confirmation([
                WorkflowTask(id="asset_query", type="asset", action="query", goal="查询净资产", input={}),
                WorkflowTask(id="invoice_query", type="invoice", action="query", goal="查询发票", input={}),
            ])
        )

    def test_asset_task_input_maps_to_workflow_state(self):
        state = asset_input({
            "input": "调整支付宝余额",
            "history": [],
            "user": None,
            "task_input": {"account_id": 7, "delta": 100},
            "task_action": "adjust_balance",
            "confirm": {},
        })

        self.assertEqual(state["intent"], "adjust_balance")
        self.assertEqual(state["target_account"], {"id": 7})

    def test_invoice_task_input_maps_to_workflow_state(self):
        state = invoice_input({
            "input": "修改发票抬头",
            "history": [],
            "user": None,
            "task_input": {"invoice_id": 9, "name": "新公司", "tax_id": "税号"},
            "task_action": "update",
            "confirm": {},
        })

        self.assertEqual(state["intent"], "update")
        self.assertEqual(state["target_invoice"], {"id": 9})
