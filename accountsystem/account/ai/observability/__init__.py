"""OpenTelemetry helpers for the Agent Runtime."""

from .telemetry import (
    add_span_event,
    get_tracer,
    init_telemetry,
    mark_span_ok,
    record_exception,
    set_span_attribute,
    set_span_attributes,
    set_span_outcome,
    start_span,
)

__all__ = [
    "add_span_event",
    "get_tracer",
    "init_telemetry",
    "mark_span_ok",
    "record_exception",
    "set_span_attribute",
    "set_span_attributes",
    "set_span_outcome",
    "start_span",
]
