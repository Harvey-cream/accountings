"""Minimal, fail-open OpenTelemetry setup for the Agent Runtime.

This module deliberately owns only technical tracing. AgentTrace remains the
product audit record and EventEmitter remains the SSE/business event channel.
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Any, Iterator

from config.dotenv_loader import env_str

logger = logging.getLogger(__name__)

_TRACER_NAME = "finpilot.agent.runtime"
_INIT_LOCK = threading.Lock()
_INITIALIZED = False
_ENABLED = False
_TRACER = None
_PROVIDER = None


class _NoOpSpan:
    def set_attribute(self, key: str, value: Any) -> None:
        return None

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        return None

    def record_exception(self, exc: BaseException) -> None:
        return None

    def set_status(self, status: Any) -> None:
        return None


_NOOP_SPAN = _NoOpSpan()


def _env_enabled() -> bool:
    return env_str("OTEL_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


def _ratio() -> float:
    try:
        value = float(env_str("OTEL_TRACES_SAMPLER_ARG", "1.0"))
    except (TypeError, ValueError):
        logger.warning("Invalid OTEL_TRACES_SAMPLER_ARG; using 1.0")
        return 1.0
    if not 0.0 <= value <= 1.0:
        logger.warning("OTEL_TRACES_SAMPLER_ARG must be between 0 and 1; using 1.0")
        return 1.0
    return value


def _build_sampler():
    from opentelemetry.sdk.trace.sampling import (
        ALWAYS_OFF,
        ALWAYS_ON,
        ParentBased,
        TraceIdRatioBased,
    )

    name = env_str("OTEL_TRACES_SAMPLER", "parentbased_traceidratio").lower().replace("-", "_")
    samplers = {
        "always_on": ALWAYS_ON,
        "always_off": ALWAYS_OFF,
        "traceidratio": TraceIdRatioBased(_ratio()),
        "parentbased_always_on": ParentBased(ALWAYS_ON),
        "parentbased_always_off": ParentBased(ALWAYS_OFF),
        "parentbased_traceidratio": ParentBased(TraceIdRatioBased(_ratio())),
    }
    sampler = samplers.get(name)
    if sampler is None:
        logger.warning("Unsupported OTEL_TRACES_SAMPLER=%s; using parentbased_traceidratio", name)
        return ParentBased(TraceIdRatioBased(_ratio()))
    return sampler


def _build_otlp_exporter(endpoint: str):
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    return OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()


def init_telemetry() -> bool:
    """Initialize tracing once. Any setup failure disables tracing and never fails a request."""
    global _INITIALIZED, _ENABLED, _TRACER, _PROVIDER

    if _INITIALIZED:
        return _ENABLED
    with _INIT_LOCK:
        if _INITIALIZED:
            return _ENABLED
        _INITIALIZED = True
        if not _env_enabled():
            return False
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create(
                {
                    "service.name": env_str("OTEL_SERVICE_NAME", "finpilot-agent"),
                    "deployment.environment": env_str("OTEL_ENVIRONMENT", "development"),
                }
            )
            provider = TracerProvider(resource=resource, sampler=_build_sampler())
            exporter = _build_otlp_exporter(env_str("OTEL_EXPORTER_OTLP_ENDPOINT"))
            provider.add_span_processor(BatchSpanProcessor(exporter))

            # Our tracer comes directly from this provider, so P1 remains reliable even if
            # an embedding process already configured a global provider.
            try:
                trace.set_tracer_provider(provider)
            except Exception:
                logger.warning("Unable to register the global OpenTelemetry provider", exc_info=True)
            _PROVIDER = provider
            _TRACER = provider.get_tracer(_TRACER_NAME)
            _ENABLED = True
        except Exception:
            _ENABLED = False
            _TRACER = None
            _PROVIDER = None
            logger.warning("OpenTelemetry initialization failed; tracing is disabled", exc_info=True)
        return _ENABLED


def get_tracer():
    """Return the runtime tracer, or a no-op tracer when telemetry is unavailable."""
    init_telemetry()
    if _TRACER is not None:
        return _TRACER
    try:
        from opentelemetry.trace import NoOpTracerProvider

        return NoOpTracerProvider().get_tracer(_TRACER_NAME)
    except Exception:
        return None


def _clean_attributes(attributes: dict[str, Any] | None) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in (attributes or {}).items():
        if value is None:
            continue
        if isinstance(value, (str, bool, int, float)):
            clean[key] = value
    return clean


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[Any]:
    """Start a current span without allowing tracer/exporter failures to affect business code."""
    if not init_telemetry():
        yield _NOOP_SPAN
        return

    manager = None
    try:
        tracer = get_tracer()
        if tracer is None:
            yield _NOOP_SPAN
            return
        manager = tracer.start_as_current_span(
            name,
            attributes=_clean_attributes(attributes),
            record_exception=False,
            set_status_on_exception=False,
        )
        span = manager.__enter__()
    except Exception:
        logger.warning("OpenTelemetry span start failed: %s", name, exc_info=True)
        yield _NOOP_SPAN
        return

    try:
        yield span
    except BaseException as exc:
        try:
            manager.__exit__(type(exc), exc, exc.__traceback__)
        except Exception:
            logger.warning("OpenTelemetry span close failed: %s", name, exc_info=True)
        raise
    else:
        try:
            manager.__exit__(None, None, None)
        except Exception:
            logger.warning("OpenTelemetry span export failed: %s", name, exc_info=True)


def set_span_attribute(span: Any, key: str, value: Any) -> None:
    if value is None or not isinstance(value, (str, bool, int, float)):
        return
    try:
        span.set_attribute(key, value)
    except Exception:
        logger.warning("OpenTelemetry attribute write failed: %s", key, exc_info=True)


def set_span_attributes(span: Any, attributes: dict[str, Any]) -> None:
    for key, value in attributes.items():
        set_span_attribute(span, key, value)


def add_span_event(span: Any, name: str, attributes: dict[str, Any] | None = None) -> None:
    try:
        span.add_event(name, attributes=_clean_attributes(attributes))
    except Exception:
        logger.warning("OpenTelemetry event write failed: %s", name, exc_info=True)


def _set_status(span: Any, *, error: bool) -> None:
    try:
        from opentelemetry.trace import Status, StatusCode

        span.set_status(Status(StatusCode.ERROR if error else StatusCode.OK))
    except Exception:
        logger.warning("OpenTelemetry status write failed", exc_info=True)


def mark_span_ok(span: Any) -> None:
    _set_status(span, error=False)


def record_exception(span: Any, exc: BaseException) -> None:
    """Record a genuine technical exception and mark the span as ERROR."""
    try:
        span.record_exception(exc)
    except Exception:
        logger.warning("OpenTelemetry exception recording failed", exc_info=True)
    _set_status(span, error=True)


def set_span_outcome(span: Any, outcome: str, *, error: bool = False) -> None:
    """Set the business outcome without treating normal waiting states as errors."""
    set_span_attribute(span, "agent.outcome", outcome)
    _set_status(span, error=error)


def _set_tracer_provider_for_tests(provider: Any) -> None:
    """Install an isolated provider used by unit tests with InMemorySpanExporter."""
    global _INITIALIZED, _ENABLED, _TRACER, _PROVIDER
    with _INIT_LOCK:
        _PROVIDER = provider
        _TRACER = provider.get_tracer(_TRACER_NAME)
        _INITIALIZED = True
        _ENABLED = True


def _reset_for_tests() -> None:
    global _INITIALIZED, _ENABLED, _TRACER, _PROVIDER
    with _INIT_LOCK:
        _INITIALIZED = False
        _ENABLED = False
        _TRACER = None
        _PROVIDER = None
