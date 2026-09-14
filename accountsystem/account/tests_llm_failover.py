"""LLM 多模型顺序兜底：FailoverLLM 的顺延 / 异常语义 / 调用面透传。

全部无网络、无 DB：用桩对象替代 ChatOpenAI，只验证兜底编排本身。
"""

from unittest.mock import patch

from django.test import SimpleTestCase

import account.ai.llm.llm as llm_module
from account.ai.llm.failover import FailoverLLM, _try_in_order


class _PrimaryDown(Exception):
    """模拟主模型 400「模型已停用」这类不可重试错误。"""


class _FallbackDown(Exception):
    """与主模型不同型，用于验证最终抛出的是「最后一个」异常。"""


class _StubBound:
    """模拟 bind_tools / with_structured_output 的返回物（Runnable）。"""

    def __init__(self, model, payload, kwargs):
        self._model = model
        self.payload = payload
        self.kwargs = kwargs

    def invoke(self, input, config=None, **kwargs):
        return self._model._reply()


class _StubModel:
    """模拟一个 ChatOpenAI：可配置失败与返回值，并记录调用次数。"""

    def __init__(self, name, *, fail_with=None, result=None):
        self.model_name = name
        self._exc = fail_with
        self._result = result
        self.invokes = 0
        self.bound_payloads = []
        self.bound_kwargs = []

    def _reply(self):
        self.invokes += 1
        if self._exc is not None:
            raise self._exc
        return self._result

    def invoke(self, input, config=None, **kwargs):
        return self._reply()

    def bind_tools(self, tools, **kwargs):
        self.bound_payloads.append(tools)
        self.bound_kwargs.append(kwargs)
        return _StubBound(self, tools, kwargs)

    def with_structured_output(self, schema, **kwargs):
        self.bound_payloads.append(schema)
        self.bound_kwargs.append(kwargs)
        return _StubBound(self, schema, kwargs)


class FailoverInvokeTests(SimpleTestCase):
    def test_primary_fails_falls_through_to_next(self):
        primary = _StubModel("gpt-5.6-luna", fail_with=_PrimaryDown("模型已停用"))
        fallback = _StubModel("claude-sonnet-4-6", result="ok")

        llm = FailoverLLM([primary, fallback])
        with self.assertLogs("account.ai.llm.failover", level="WARNING") as logs:
            self.assertEqual(llm.invoke("hi"), "ok")

        self.assertEqual(primary.invokes, 1)
        self.assertEqual(fallback.invokes, 1)
        self.assertIn("gpt-5.6-luna", "\n".join(logs.output))

    def test_primary_success_skips_fallbacks(self):
        primary = _StubModel("gpt-5.6-luna", result="primary")
        fallback = _StubModel("claude-sonnet-4-6", result="fallback")

        llm = FailoverLLM([primary, fallback])
        self.assertEqual(llm.invoke("hi"), "primary")
        self.assertEqual(primary.invokes, 1)
        self.assertEqual(fallback.invokes, 0)

    def test_third_model_rescues_when_two_fail(self):
        m1 = _StubModel("gpt-5.6-luna", fail_with=_PrimaryDown("disabled"))
        m2 = _StubModel("claude-sonnet-4-6", fail_with=_PrimaryDown("disabled"))
        m3 = _StubModel("gemini-3.7-flash", result="gemini")

        llm = FailoverLLM([m1, m2, m3])
        with self.assertLogs("account.ai.llm.failover", level="WARNING"):
            self.assertEqual(llm.invoke("hi"), "gemini")
        self.assertEqual([m.invokes for m in (m1, m2, m3)], [1, 1, 1])

    def test_all_fail_reraises_last_exception_type(self):
        primary = _StubModel("gpt-5.6-luna", fail_with=_PrimaryDown("disabled"))
        fallback = _StubModel("claude-sonnet-4-6", fail_with=_FallbackDown("timeout"))

        llm = FailoverLLM([primary, fallback])
        with self.assertLogs("account.ai.llm.failover", level="WARNING"):
            with self.assertRaises(_FallbackDown):
                llm.invoke("hi")

    def test_config_only_forwarded_when_provided(self):
        seen = {}

        class _Recorder(_StubModel):
            def invoke(self, input, config=None, **kwargs):
                seen["config"] = config
                seen["kwargs"] = kwargs
                return "ok"

        llm = FailoverLLM([_Recorder("gpt-5.6-luna", result="ok")])
        llm.invoke("hi")
        self.assertIsNone(seen["config"])
        self.assertEqual(seen["kwargs"], {})

    def test_plain_invoke_keeps_none_semantics(self):
        """普通 invoke 不把 None 当失败——None-as-failure 只在绑定路径启用。"""
        primary = _StubModel("gpt-5.6-luna", result=None)
        fallback = _StubModel("claude-sonnet-4-6", result="ok")

        llm = FailoverLLM([primary, fallback])
        self.assertIsNone(llm.invoke("hi"))
        self.assertEqual(primary.invokes, 1)
        self.assertEqual(fallback.invokes, 0)


class FailoverBindingTests(SimpleTestCase):
    def test_bind_tools_falls_through(self):
        primary = _StubModel("gpt-5.6-luna", fail_with=_PrimaryDown("disabled"))
        fallback = _StubModel("claude-sonnet-4-6", result="tool-reply")

        bound = FailoverLLM([primary, fallback]).bind_tools(["t1"], tool_choice="auto")
        with self.assertLogs("account.ai.llm.failover", level="WARNING"):
            self.assertEqual(bound.invoke(["msg"]), "tool-reply")

        self.assertEqual(primary.bound_payloads, [["t1"]])
        self.assertEqual(fallback.bound_payloads, [["t1"]])
        # bind_tools 的 kwargs 必须逐个透传到每个模型
        self.assertEqual(primary.bound_kwargs, [{"tool_choice": "auto"}])
        self.assertEqual(fallback.bound_kwargs, [{"tool_choice": "auto"}])

    def test_with_structured_output_falls_through_and_forwards_kwargs(self):
        primary = _StubModel("gpt-5.6-luna", fail_with=_PrimaryDown("disabled"))
        fallback = _StubModel("claude-sonnet-4-6", result={"amount": 30})

        bound = FailoverLLM([primary, fallback]).with_structured_output(
            "WorkflowPlan", method="function_calling"
        )
        with self.assertLogs("account.ai.llm.failover", level="WARNING"):
            self.assertEqual(bound.invoke(["msg"]), {"amount": 30})

        # nested_structured_output 依赖 method 透传，两个模型都要收到
        self.assertEqual(primary.bound_kwargs, [{"method": "function_calling"}])
        self.assertEqual(fallback.bound_kwargs, [{"method": "function_calling"}])

    def test_structured_output_none_falls_through_to_next(self):
        """模型未产出 tool call 时 langchain 返回 None 而非抛异常，必须继续顺延。"""
        primary = _StubModel("gpt-5.6-luna", result=None)
        fallback = _StubModel("claude-sonnet-4-6", result={"amount": 30})

        bound = FailoverLLM([primary, fallback]).with_structured_output("WorkflowPlan")
        with self.assertLogs("account.ai.llm.failover", level="WARNING") as logs:
            self.assertEqual(bound.invoke(["msg"]), {"amount": 30})

        self.assertEqual(primary.invokes, 1)
        self.assertEqual(fallback.invokes, 1)
        self.assertIn("gpt-5.6-luna", "\n".join(logs.output))

    def test_bind_tools_none_falls_through_to_next(self):
        primary = _StubModel("gpt-5.6-luna", result=None)
        fallback = _StubModel("claude-sonnet-4-6", result="tool-reply")

        bound = FailoverLLM([primary, fallback]).bind_tools(["t1"])
        with self.assertLogs("account.ai.llm.failover", level="WARNING"):
            self.assertEqual(bound.invoke(["msg"]), "tool-reply")

    def test_structured_output_all_none_raises(self):
        primary = _StubModel("gpt-5.6-luna", result=None)
        fallback = _StubModel("claude-sonnet-4-6", result=None)

        bound = FailoverLLM([primary, fallback]).with_structured_output("WorkflowPlan")
        with self.assertLogs("account.ai.llm.failover", level="WARNING"):
            with self.assertRaises(ValueError):
                bound.invoke(["msg"])


class FailoverGuardTests(SimpleTestCase):
    def test_empty_model_list_rejected(self):
        with self.assertRaises(ValueError):
            FailoverLLM([])
        with self.assertRaises(ValueError):
            _try_in_order([])

    def test_model_names_property(self):
        llm = FailoverLLM([_StubModel("a"), _StubModel("b")])
        self.assertEqual(llm.model_names, ["a", "b"])


class ModelChainTests(SimpleTestCase):
    def test_chain_is_primary_then_fallbacks(self):
        with patch.object(llm_module, "LLM_AGENT_FALLBACK_MODELS", ["claude", "gemini"]):
            self.assertEqual(llm_module._model_chain("luna"), ["luna", "claude", "gemini"])

    def test_chain_dedupes_primary_in_fallback_list(self):
        with patch.object(llm_module, "LLM_AGENT_FALLBACK_MODELS", ["claude", "luna", "gemini"]):
            self.assertEqual(llm_module._model_chain("luna"), ["luna", "claude", "gemini"])
            # 换个主模型时 luna 回到兜底位，顺序仍按兜底列表
            self.assertEqual(llm_module._model_chain("claude"), ["claude", "luna", "gemini"])

    def test_chain_single_model_when_no_fallbacks(self):
        with patch.object(llm_module, "LLM_AGENT_FALLBACK_MODELS", []):
            self.assertEqual(llm_module._model_chain("luna"), ["luna"])

    def test_split_models_parsing(self):
        self.assertEqual(llm_module._split_models(""), [])
        self.assertEqual(llm_module._split_models("  "), [])
        self.assertEqual(llm_module._split_models(" a , b "), ["a", "b"])
        self.assertEqual(llm_module._split_models("a,a,b"), ["a", "b"])
        self.assertEqual(llm_module._split_models("a,,b"), ["a", "b"])
