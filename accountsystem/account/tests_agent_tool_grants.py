"""D2 安全收口回归：查询态节点永不绑定/调用写工具。

全部无网络、无 DB：用桩模型记录 bind_tools 的载荷，用桩工具对象提供 .name。
覆盖四域 agent 节点 + 工具授权策略本身。
"""

from django.test import SimpleTestCase
from langchain_core.messages import AIMessage, HumanMessage

from account.ai.agents.supervisor.asset.asset_nodes import make_asset_agent_node
from account.ai.agents.supervisor.bill.bill_nodes import make_bill_agent_node
from account.ai.agents.supervisor.budget.budget_nodes import make_budget_agent_node
from account.ai.agents.supervisor.invoice.invoice_nodes import make_invoice_agent_node
from account.ai.tools.tool_policy import (
    BLOCKED_MESSAGE,
    READ_TOOLS,
    WRITE_TOOLS,
    allowed_tool_names,
)


def _write_names(domain: str) -> set[str]:
    return {name for group in WRITE_TOOLS[domain].values() for name in group}


def _tools(domain: str) -> list:
    """按真实工具名造桩工具（含预算域的知识库检索），不需要 user / DB。"""
    names = [*READ_TOOLS[domain], *_write_names(domain)]
    if domain == "budget":
        names.append("search_finance_knowledge")
    return [_StubTool(name) for name in dict.fromkeys(names)]


class _StubTool:
    def __init__(self, name: str):
        self.name = name


class _StubBound:
    def __init__(self, reply):
        self._reply = reply

    def invoke(self, input, config=None, **kwargs):
        return self._reply


class _StubModel:
    """记录每次 bind_tools 绑定的工具名，invoke 返回预设 reply。"""

    def __init__(self, reply=None):
        self.bound: list[list[str]] = []
        self._reply = reply if reply is not None else AIMessage(content="ok")

    def bind_tools(self, tools, **kwargs):
        self.bound.append([t.name for t in tools])
        return _StubBound(self._reply)


# ----- 策略层：白名单本身 -----

class ToolGrantPolicyTests(SimpleTestCase):
    def test_query_intent_is_read_only_in_every_domain(self):
        for domain, action in (
            ("bill", "query"),
            ("budget", "query_budget"),
            ("budget", "budget_advice"),
            ("asset", "query"),
            ("invoice", "query"),
        ):
            names = allowed_tool_names(domain, action, False)
            self.assertEqual(set(names), set(READ_TOOLS[domain]), (domain, action, names))

    def test_unconfirmed_write_intent_stays_read_only(self):
        """Planner 就算把写意图标成写 action，未确认也只读。"""
        for domain, action in (
            ("bill", "create"),
            ("bill", "batch_create"),
            ("bill", "update"),
            ("bill", "delete"),
            ("budget", "set_budget"),
            ("asset", "create"),
            ("asset", "update"),
            ("asset", "delete"),
            ("asset", "adjust_balance"),
            ("invoice", "create"),
            ("invoice", "update"),
            ("invoice", "delete"),
        ):
            names = allowed_tool_names(domain, action, False)
            self.assertFalse(set(names) & _write_names(domain), (domain, action, names))

    def test_confirmed_write_intent_grants_only_its_own_action(self):
        for domain, action, expected in (
            ("bill", "create", {"create_bill"}),
            ("bill", "batch_create", {"batch_create_bills"}),
            ("bill", "update", {"update_bill"}),
            ("bill", "delete", {"delete_bill"}),
            ("budget", "set_budget", {"create_budget", "update_budget"}),
            ("asset", "create", {"create_asset_account"}),
            ("asset", "update", {"update_asset_account"}),
            ("asset", "delete", {"delete_asset_account"}),
            ("asset", "adjust_balance", {"adjust_asset_balance"}),
            ("invoice", "create", {"create_invoice"}),
            ("invoice", "update", {"update_invoice"}),
            ("invoice", "delete", {"delete_invoice"}),
        ):
            names = set(allowed_tool_names(domain, action, True))
            self.assertEqual(names - set(READ_TOOLS[domain]), expected, (domain, action, names))

    def test_no_domain_has_an_unconfirmed_write_exception(self):
        """批次二起发票新建也走确认卡，四个域都不再存在"未确认也可写"的例外。"""
        for domain, actions in WRITE_TOOLS.items():
            for action in actions:
                names = set(allowed_tool_names(domain, action, False))
                self.assertFalse(names & _write_names(domain), (domain, action, names))

    def test_always_tools_are_added_and_deduped(self):
        names = allowed_tool_names(
            "budget", "query_budget", False, always=("search_finance_knowledge", "query_budget")
        )
        self.assertEqual(names, ("query_budget", "budget_advice", "search_finance_knowledge"))

    def test_unknown_domain_or_intent_yields_empty_grant(self):
        self.assertEqual(allowed_tool_names("nope", "query", False), ())
        self.assertEqual(allowed_tool_names("bill", "nope", True), READ_TOOLS["bill"])


# ----- 节点层：绑定载荷 -----

class BillAgentNodeGrantTests(SimpleTestCase):
    def _node(self, model):
        return make_bill_agent_node(_tools("bill"), model=model)

    def test_query_binds_read_only(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "query",
                "confirmed": False,
                "messages": [HumanMessage(content="看看我这个月花了多少钱")],
                "loops": 0,
            }
        )
        self.assertEqual(model.bound[-1], ["query_bills", "search_bills"])

    def test_unconfirmed_create_binds_no_write_tool(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "create",
                "confirmed": False,
                "task_input": {"amount": 30},
                "messages": [HumanMessage(content="午饭30")],
                "loops": 0,
            }
        )
        self.assertNotIn("create_bill", model.bound[-1])

    def test_confirmed_create_binds_create_only(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "create",
                "confirmed": True,
                "task_input": {"amount": 30},
                "messages": [HumanMessage(content="午饭30")],
                "loops": 0,
            }
        )
        bound = set(model.bound[-1])
        self.assertIn("create_bill", bound)
        self.assertNotIn("update_bill", bound)
        self.assertNotIn("delete_bill", bound)

    def test_confirmed_update_cannot_reach_delete(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "update",
                "confirmed": True,
                "task_input": {"bill_id": 7, "amount": 80},
                "messages": [HumanMessage(content="把昨天那笔50改成80")],
                "loops": 0,
            }
        )
        bound = set(model.bound[-1])
        self.assertEqual(bound - set(READ_TOOLS["bill"]), {"update_bill"})


class InvoiceAgentNodeGrantTests(SimpleTestCase):
    def _node(self, model):
        return make_invoice_agent_node(_tools("invoice"), model=model)

    def test_query_binds_read_only(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "query",
                "confirmed": False,
                "messages": [HumanMessage(content="我有哪些发票")],
                "loops": 0,
            }
        )
        self.assertEqual(model.bound[-1], list(READ_TOOLS["invoice"]))

    def test_unconfirmed_update_has_no_write_tool(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "update",
                "confirmed": False,
                "messages": [HumanMessage(content="把那张发票金额改成1500")],
                "loops": 0,
            }
        )
        self.assertNotIn("update_invoice", model.bound[-1])

    def test_unconfirmed_create_binds_no_write_tool(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "create",
                "confirmed": False,
                "task_input": {"name": "某某科技公司", "tax_id": "91310000MA1FL0XXXX"},
                "messages": [HumanMessage(content="开一张发票")],
                "loops": 0,
            }
        )
        bound = set(model.bound[-1])
        self.assertNotIn("create_invoice", bound)
        self.assertNotIn("delete_invoice", bound)

    def test_confirmed_create_binds_create_only(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "create",
                "confirmed": True,
                "task_input": {"name": "某某科技公司", "tax_id": "91310000MA1FL0XXXX"},
                "messages": [HumanMessage(content="开一张发票")],
                "loops": 0,
            }
        )
        bound = set(model.bound[-1])
        self.assertEqual(bound - set(READ_TOOLS["invoice"]), {"create_invoice"})


class AssetAgentNodeGrantTests(SimpleTestCase):
    def _node(self, model):
        return make_asset_agent_node(_tools("asset"), model=model)

    def test_query_binds_read_only(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "query",
                "confirmed": False,
                "messages": [HumanMessage(content="我都有哪些资产账户")],
                "loops": 0,
            }
        )
        self.assertEqual(model.bound[-1], list(READ_TOOLS["asset"]))

    def test_unconfirmed_adjust_has_no_write_tool(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "adjust_balance",
                "confirmed": False,
                "messages": [HumanMessage(content="支付宝余额减少500")],
                "loops": 0,
            }
        )
        self.assertNotIn("adjust_asset_balance", model.bound[-1])

    def test_confirmed_adjust_binds_adjust_only(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "adjust_balance",
                "confirmed": True,
                "messages": [HumanMessage(content="支付宝余额减少500")],
                "loops": 0,
            }
        )
        bound = set(model.bound[-1])
        self.assertEqual(bound - set(READ_TOOLS["asset"]), {"adjust_asset_balance"})


class BudgetAgentNodeGrantTests(SimpleTestCase):
    def _node(self, model):
        return make_budget_agent_node(_tools("budget"), model=model)

    def test_query_binds_read_only_plus_knowledge(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "query_budget",
                "confirmed": False,
                "budget_params": {"period": "2026-09", "budget_type": "month"},
                "messages": [HumanMessage(content="我这个月预算还剩多少")],
                "loops": 0,
            }
        )
        bound = set(model.bound[-1])
        self.assertIn("search_finance_knowledge", bound)
        self.assertNotIn("create_budget", bound)
        self.assertNotIn("update_budget", bound)

    def test_unconfirmed_set_budget_has_no_write_tool(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "set_budget",
                "confirmed": False,
                "budget_params": {"amount": 8000, "period": "2026-09", "budget_type": "month"},
                "messages": [HumanMessage(content="这个月总预算设成8000")],
                "loops": 0,
            }
        )
        bound = set(model.bound[-1])
        self.assertNotIn("create_budget", bound)
        self.assertNotIn("update_budget", bound)

    def test_confirmed_set_budget_binds_write_tools(self):
        model = _StubModel()
        self._node(model)(
            {
                "intent": "set_budget",
                "confirmed": True,
                "budget_params": {"amount": 8000, "period": "2026-09", "budget_type": "month"},
                "messages": [HumanMessage(content="这个月总预算设成8000")],
                "loops": 0,
            }
        )
        bound = set(model.bound[-1])
        self.assertIn("create_budget", bound)
        self.assertIn("update_budget", bound)


# ----- 第二道闸：越权 tool_call 被拒 -----

class MutationHardGateTests(SimpleTestCase):
    """即使 LLM 越过白名单发出写工具调用，也必须被节点拒绝、不下发工具。"""

    def _denied_reply(self, name, args):
        return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": "call-1"}])

    def _assert_blocked(self, out):
        self.assertEqual(out["result"]["message"], BLOCKED_MESSAGE)
        self.assertTrue(out["result"]["data"]["needs_input"])
        self.assertFalse(out["result"]["success"])
        for msg in out["messages"]:
            self.assertFalse(getattr(msg, "tool_calls", None), "越权 tool_call 不得进入 messages")

    def test_bill_query_refuses_delete_call(self):
        with self.assertLogs("account.ai.tools.tool_policy", level="WARNING"):
            out = make_bill_agent_node(
                _tools("bill"), model=_StubModel(reply=self._denied_reply("delete_bill", {"bill_id": 1}))
            )(
                {
                    "intent": "query",
                    "confirmed": False,
                    "messages": [HumanMessage(content="删掉我最近一笔打车记录")],
                    "loops": 0,
                }
            )
        self._assert_blocked(out)

    def test_invoice_query_refuses_update_call(self):
        with self.assertLogs("account.ai.tools.tool_policy", level="WARNING"):
            out = make_invoice_agent_node(
                _tools("invoice"),
                model=_StubModel(reply=self._denied_reply("update_invoice", {"invoice_id": 1, "amount": 1500})),
            )(
                {
                    "intent": "query",
                    "confirmed": False,
                    "messages": [HumanMessage(content="把那张发票金额改成1500")],
                    "loops": 0,
                }
            )
        self._assert_blocked(out)

    def test_asset_and_budget_refuse_out_of_grant_writes(self):
        cases = [
            (
                make_asset_agent_node,
                "asset",
                "delete_asset_account",
                {"intent": "query", "confirmed": False},
            ),
            (
                make_budget_agent_node,
                "budget",
                "create_budget",
                {"intent": "query_budget", "confirmed": False, "budget_params": {"period": "2026-09"}},
            ),
        ]
        for factory, domain, tool_name, extra in cases:
            with self.subTest(domain=domain):
                state = {
                    "messages": [HumanMessage(content="随便问一句")],
                    "loops": 0,
                    **extra,
                }
                with self.assertLogs("account.ai.tools.tool_policy", level="WARNING"):
                    out = factory(
                        _tools(domain), model=_StubModel(reply=self._denied_reply(tool_name, {}))
                    )(state)
                self._assert_blocked(out)

    def test_authorized_call_is_not_blocked(self):
        """白名单内的工具调用照常下发，闸门不误伤。"""
        reply = AIMessage(content="", tool_calls=[{"name": "query_bills", "args": {}, "id": "call-2"}])
        out = make_bill_agent_node(_tools("bill"), model=_StubModel(reply=reply))(
            {
                "intent": "query",
                "confirmed": False,
                "messages": [HumanMessage(content="看看账单")],
                "loops": 0,
            }
        )
        self.assertNotIn("result", out)
        self.assertTrue(out["messages"][-1].tool_calls)
