"""批次二回归：D1 语义定位 / D3 schema 细节 + 文本污染 / D5 缺参不下发确认卡。

全部无网络、无 DB：只测 schema 校验、计划归一化与 executor 的纯函数。
"""

from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase
from pydantic import ValidationError

from account.ai.orchestrator import executor
from account.ai.orchestrator.task_schema import (
    AssetAdjustBalanceInput,
    AssetDeleteInput,
    AssetUpdateInput,
    BillQueryInput,
    InvoiceDeleteInput,
    InvoiceUpdateInput,
    WorkflowPlan,
    WorkflowTask,
)
from account.ai.tools.finance_tools.bill_tools import _period_range, query_bills_tool


# ----- D1：asset / invoice 目标 id 放宽 + 语义定位字段 -----


class AssetLocatorSchemaTests(SimpleTestCase):
    def test_update_accepts_keyword_locator_without_id(self):
        payload = AssetUpdateInput(keyword="招商银行", balance=5000)
        self.assertIsNone(payload.account_id)
        self.assertEqual(payload.balance, 5000)

    def test_update_accepts_explicit_id(self):
        self.assertEqual(AssetUpdateInput(account_id=3, balance=5000).account_id, 3)

    def test_update_requires_a_locator(self):
        with self.assertRaises(ValidationError):
            AssetUpdateInput(balance=5000)

    def test_update_requires_a_changed_field(self):
        with self.assertRaises(ValidationError):
            AssetUpdateInput(keyword="招商银行")

    def test_name_is_a_change_field_not_a_locator(self):
        """只给 name 不给 keyword 时仍算缺定位条件。"""
        with self.assertRaises(ValidationError):
            AssetUpdateInput(name="建设银行")

    def test_delete_and_adjust_accept_keyword(self):
        self.assertIsNone(AssetDeleteInput(keyword="招商银行").account_id)
        self.assertEqual(AssetAdjustBalanceInput(keyword="支付宝", delta=-500).delta, -500)
        with self.assertRaises(ValidationError):
            AssetDeleteInput()
        with self.assertRaises(ValidationError):
            AssetAdjustBalanceInput(delta=100)


class InvoiceLocatorSchemaTests(SimpleTestCase):
    def test_update_accepts_keyword_without_id(self):
        payload = InvoiceUpdateInput(keyword="某某科技", amount=1500)
        self.assertIsNone(payload.invoice_id)
        self.assertEqual(payload.amount, 1500)

    def test_update_requires_locator_and_change(self):
        with self.assertRaises(ValidationError):
            InvoiceUpdateInput(amount=1500)
        with self.assertRaises(ValidationError):
            InvoiceUpdateInput(keyword="某某科技")

    def test_delete_accepts_keyword(self):
        self.assertEqual(InvoiceDeleteInput(keyword="某某科技").keyword, "某某科技")
        with self.assertRaises(ValidationError):
            InvoiceDeleteInput()


# ----- D3：bill 查询字段 + WorkflowPlan id 归一化 + reason 容忍 -----


class BillQueryFieldTests(SimpleTestCase):
    def test_query_input_accepts_period_date_exclude_category(self):
        payload = BillQueryInput(period="2026-09", exclude_category="餐饮")
        self.assertEqual(payload.period, "2026-09")
        self.assertEqual(payload.exclude_category, "餐饮")
        self.assertEqual(BillQueryInput(date="2026-09-15").date, "2026-09-15")

    def test_period_range_expands_month_and_year(self):
        self.assertEqual(_period_range("2026-09"), (date(2026, 9, 1), date(2026, 9, 30)))
        self.assertEqual(_period_range("2026-12"), (date(2026, 12, 1), date(2026, 12, 31)))
        self.assertEqual(_period_range("2026"), (date(2026, 1, 1), date(2026, 12, 31)))
        self.assertEqual(_period_range("2024-02"), (date(2024, 2, 1), date(2024, 2, 29)))
        self.assertEqual(_period_range(None), (None, None))
        with self.assertRaises(Exception):
            _period_range("2026/09")


class QueryBillsRangeTests(SimpleTestCase):
    """工具层日期优先级：精确 date > period > 显式 start/end；都没有才回落 days。"""

    def _call(self, **kwargs):
        with patch("account.ai.tools.finance_tools.bill_tools.expense_service") as svc:
            svc.search_expense.return_value = []
            svc.query_expense.return_value = []
            query_bills_tool(user=None).func(**kwargs)
            return svc

    def test_exact_date_wins(self):
        svc = self._call(date="2026-09-15", period="2026-09")
        args = svc.search_expense.call_args.kwargs
        self.assertEqual((args["start_date"], args["end_date"]), (date(2026, 9, 15), date(2026, 9, 15)))

    def test_period_used_when_no_exact_date(self):
        svc = self._call(period="2026-09")
        args = svc.search_expense.call_args.kwargs
        self.assertEqual((args["start_date"], args["end_date"]), (date(2026, 9, 1), date(2026, 9, 30)))

    def test_explicit_range_used_last(self):
        svc = self._call(start_date="2026-09-01", end_date="2026-09-10")
        args = svc.search_expense.call_args.kwargs
        self.assertEqual((args["start_date"], args["end_date"]), (date(2026, 9, 1), date(2026, 9, 10)))

    def test_exclude_category_is_passed_through(self):
        svc = self._call(period="2026-09", exclude_category="餐饮")
        self.assertEqual(svc.search_expense.call_args.kwargs["exclude_category_name"], "餐饮")

    def test_no_filter_falls_back_to_recent_days(self):
        svc = self._call()
        svc.query_expense.assert_called_once()
        svc.search_expense.assert_not_called()


class StrictInputToleranceTests(SimpleTestCase):
    def test_reason_is_tolerated_and_stripped_from_dump(self):
        task = WorkflowTask(
            id="b1",
            type="bill",
            action="create",
            input={"amount": 30, "reason": "用户说午饭"},
        )
        self.assertNotIn("reason", task.input)
        self.assertEqual(task.input["amount"], 30)

    def test_unknown_business_field_is_rejected(self):
        with self.assertRaises(ValidationError):
            WorkflowTask(id="b1", type="bill", action="create", input={"amount": 30, "bogus": 1})


class WorkflowPlanIdNormalizationTests(SimpleTestCase):
    def test_missing_ids_are_filled(self):
        plan = WorkflowPlan(
            tasks=[
                {"type": "bill", "action": "query", "input": {}},
                {"type": "chat", "action": "respond", "input": {"message": "你好"}},
            ]
        )
        ids = [task.id for task in plan.tasks]
        self.assertEqual(len(set(ids)), 2)
        self.assertTrue(all(ids))

    def test_numeric_ids_are_stringified_and_references_kept(self):
        plan = WorkflowPlan(
            tasks=[
                {"id": 1, "type": "bill", "action": "query", "input": {}},
                {"id": 2, "type": "chat", "action": "respond", "input": {"message": "你好"}, "depends_on": [1]},
            ]
        )
        self.assertEqual([task.id for task in plan.tasks], ["1", "2"])
        self.assertEqual(plan.tasks[1].depends_on, ["1"])

    def test_filled_ids_do_not_collide_with_existing(self):
        plan = WorkflowPlan(
            tasks=[
                {"id": "task_1", "type": "bill", "action": "query", "input": {}},
                {"type": "chat", "action": "respond", "input": {"message": "你好"}},
            ]
        )
        self.assertEqual(len({task.id for task in plan.tasks}), 2)

    def test_unknown_dependency_still_rejected(self):
        with self.assertRaises(ValidationError):
            WorkflowPlan(
                tasks=[
                    {"type": "chat", "action": "respond", "input": {"message": "你好"}, "depends_on": ["nope"]}
                ]
            )


# ----- D5：缺参不预览，交给 Workflow 追问 -----


def _task(type_, action, **payload):
    return WorkflowTask(id=f"{type_}_{action}", type=type_, action=action, input=payload)


class PreviewGateTests(SimpleTestCase):
    def test_incomplete_writes_are_not_previewable(self):
        cases = [
            _task("bill", "create", category="餐饮"),                       # 缺 amount
            _task("budget", "set_budget", period="2026-09"),                # 缺 amount
            _task("asset", "create", name="招商银行"),                       # 缺 asset_type
            _task("invoice", "create", name="某某科技"),                     # 缺 tax_id
        ]
        for task in cases:
            with self.subTest(task=f"{task.type}.{task.action}"):
                self.assertFalse(executor._has_previewable_action([task]))

    def test_complete_writes_are_previewable(self):
        cases = [
            _task("bill", "create", amount=30),
            _task("budget", "set_budget", amount=8000, period="2026-09"),
            _task("asset", "create", name="招商银行", asset_type="储蓄卡"),
            _task("invoice", "create", name="某某科技", tax_id="91310000MA1FL0XXXX"),
        ]
        for task in cases:
            with self.subTest(task=f"{task.type}.{task.action}"):
                self.assertTrue(executor._has_previewable_action([task]))

    def test_todo_resolution_writes_stay_unpreviewed(self):
        """有 id 的定向写可以预览；只有 keyword 的必须先去 Workflow 定位。"""
        self.assertTrue(executor._has_previewable_action([_task("asset", "update", account_id=3, balance=5000)]))
        self.assertFalse(executor._has_previewable_action([_task("asset", "update", keyword="招商银行", balance=5000)]))
        self.assertFalse(executor._has_previewable_action([_task("invoice", "delete", keyword="某某科技")]))
        self.assertTrue(executor._has_previewable_action([_task("invoice", "delete", invoice_id=9)]))

    def test_confirmation_payload_skips_incomplete_writes(self):
        ordered = [_task("bill", "create", amount=30), _task("budget", "set_budget", period="2026-09")]
        confirm = executor._build_plan_confirmation(ordered)
        actions = [(c["entity"], c["action"]) for c in confirm["confirmations"]]
        self.assertEqual(actions, [("bill", "create")])


# ----- D3：goal 为空时不得回落到整句 user_input -----


class TaskInputScopingTests(SimpleTestCase):
    def test_empty_goal_uses_task_scoped_text(self):
        task = _task("chat", "respond", message="你好呀")
        self.assertEqual(executor._task_input(task, {}), "你好呀")

    def test_empty_goal_falls_back_to_type_action_label(self):
        task = _task("bill", "query")
        self.assertEqual(executor._task_input(task, {}), "执行 bill.query 任务")

    def test_explicit_goal_is_kept_and_prev_results_appended(self):
        task = WorkflowTask(
            id="t2",
            type="bill",
            action="query",
            goal="统计本月餐饮支出",
            input={},
            depends_on=["t1"],
        )
        text = executor._task_input(task, {"t1": {"output": "上月餐饮 500 元"}})
        self.assertTrue(text.startswith("统计本月餐饮支出"))
        self.assertIn("上月餐饮 500 元", text)
