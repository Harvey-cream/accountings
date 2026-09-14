"""多模型顺序兜底：主模型失败自动顺延到下一个模型。

同一 OpenAI 兼容端点下按顺序尝试 [主模型, 兜底1, 兜底2...]；某模型报错
（停用 / 超时 / 限流 / 鉴权 / 结构化输出解析失败）只跳过该模型，不影响后续
模型；全部失败才抛出**最后一个**异常（保留原异常类型，上层据此分类）。

保持 LangChain 调用面：invoke / bind_tools / with_structured_output。
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Any

logger = logging.getLogger(__name__)


def _try_in_order(
    attempts: Sequence[tuple[str, Callable[[], Any]]],
    *,
    treat_none_as_failure: bool = False,
) -> Any:
    """按序执行 attempts；返回首个成功结果；全部失败抛出最后一个异常。

    attempts: [(model_name, callable)]，model_name 仅用于日志。
    treat_none_as_failure: 结构化输出 / 工具绑定场景下，模型未产出 tool call 时
    langchain 返回 None 而**不抛异常**；此时必须视为「该模型失败」继续顺延，
    否则兜底链会在 None 处静默断掉（后续模型永不尝试）。
    """
    if not attempts:
        raise ValueError("no LLM models configured")

    last_exc: BaseException | None = None
    for idx, (name, call) in enumerate(attempts):
        has_next = idx + 1 < len(attempts)
        try:
            result = call()
        except Exception as exc:
            last_exc = exc
            if has_next:
                logger.warning(
                    "LLM fallback: model=%s failed (%s: %s), trying next",
                    name,
                    type(exc).__name__,
                    exc,
                )
            continue
        if treat_none_as_failure and result is None:
            last_exc = ValueError(f"model={name} returned no structured output")
            if has_next:
                logger.warning(
                    "LLM fallback: model=%s returned no structured output, trying next",
                    name,
                )
            continue
        return result
    raise last_exc  # type: ignore[misc]


def _invoke_thunk(runnable: Any, input: Any, config: Any, kwargs: dict) -> Callable[[], Any]:
    """把「一次 invoke」包成零参可调用；config 为 None 时不传，避免污染 Runnable。"""
    if config is None:
        return lambda: runnable.invoke(input, **kwargs)
    return lambda: runnable.invoke(input, config=config, **kwargs)


class _FailoverRunnable:
    """一组已绑定（tools / structured_output）的 Runnable，按序兜底 invoke。

    绑定路径把 None 视为失败：模型不产出 tool call 时 langchain 返回 None，
    若当成功返回会截断兜底链。
    """

    def __init__(self, entries: Sequence[tuple[str, Any]]) -> None:
        self._entries = list(entries)

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        return _try_in_order(
            [
                (name, _invoke_thunk(runnable, input, config, kwargs))
                for name, runnable in self._entries
            ],
            treat_none_as_failure=True,
        )


class FailoverLLM:
    """多模型顺序兜底包装，API 与非兜底 LLM 实例一致。"""

    def __init__(self, models: Sequence[Any]) -> None:
        if not models:
            raise ValueError("FailoverLLM requires at least one model")
        self._models = list(models)

    @property
    def model_names(self) -> list[str]:
        return [getattr(m, "model_name", "?") for m in self._models]

    def _named(self) -> list[tuple[str, Any]]:
        return [(getattr(m, "model_name", "?"), m) for m in self._models]

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        return _try_in_order(
            [
                (name, _invoke_thunk(model, input, config, kwargs))
                for name, model in self._named()
            ]
        )

    def bind_tools(self, tools: Any, **kwargs: Any) -> _FailoverRunnable:
        return _FailoverRunnable(
            [(name, model.bind_tools(tools, **kwargs)) for name, model in self._named()]
        )

    def with_structured_output(self, schema: Any, **kwargs: Any) -> _FailoverRunnable:
        return _FailoverRunnable(
            [
                (name, model.with_structured_output(schema, **kwargs))
                for name, model in self._named()
            ]
        )
