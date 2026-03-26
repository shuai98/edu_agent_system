"""Service layer for tracing and long-term memory."""

from .memory import memory_store
from .tracing import (
    attach_trace,
    begin_trace,
    current_trace_id,
    end_trace,
    get_trace,
    initialize_tracing,
    reset_trace,
    trace_span,
)

__all__ = [
    "attach_trace",
    "begin_trace",
    "current_trace_id",
    "end_trace",
    "get_trace",
    "initialize_tracing",
    "memory_store",
    "reset_trace",
    "trace_span",
]
