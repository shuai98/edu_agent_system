"""Request tracing with in-memory spans and optional OpenTelemetry export."""

from __future__ import annotations

import os
import threading
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar, Token
from copy import deepcopy
from typing import Any, Dict, Iterator, Optional

from loguru import logger

_trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_span_stack_ctx: ContextVar[tuple[str, ...]] = ContextVar("span_stack", default=())
_traces: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()
_initialized = False
_otel_tracer = None


def _sanitize_attributes(attributes: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    for key, value in (attributes or {}).items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean


def initialize_tracing() -> None:
    global _initialized, _otel_tracer
    if _initialized:
        return
    _initialized = True

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
    except ImportError:
        logger.warning("Tracing fallback: OpenTelemetry packages are not installed.")
        return

    resource = Resource.create(
        {"service.name": os.getenv("OTEL_SERVICE_NAME", "edureflex-api")}
    )
    provider = TracerProvider(resource=resource)

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))

    if os.getenv("TRACE_CONSOLE", "false").lower() == "true":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _otel_tracer = trace.get_tracer("edureflex")


def begin_trace(metadata: Optional[Dict[str, Any]] = None) -> tuple[str, tuple[Token, Token]]:
    initialize_tracing()
    trace_id = uuid.uuid4().hex
    trace_token = _trace_id_ctx.set(trace_id)
    stack_token = _span_stack_ctx.set(())
    with _lock:
        _traces[trace_id] = {
            "trace_id": trace_id,
            "status": "running",
            "started_at": time.time(),
            "ended_at": None,
            "duration_ms": None,
            "metadata": _sanitize_attributes(metadata),
            "spans": [],
        }
    return trace_id, (trace_token, stack_token)


def attach_trace(trace_id: str) -> tuple[Token, Token]:
    trace_token = _trace_id_ctx.set(trace_id)
    stack_token = _span_stack_ctx.set(())
    return trace_token, stack_token


def reset_trace(token: Token | tuple[Token, Token]) -> None:
    if isinstance(token, tuple):
        trace_token, stack_token = token
        _span_stack_ctx.reset(stack_token)
        _trace_id_ctx.reset(trace_token)
        return
    _trace_id_ctx.reset(token)


def current_trace_id() -> str:
    return _trace_id_ctx.get() or ""


def end_trace(status: str = "ok", metadata: Optional[Dict[str, Any]] = None) -> None:
    trace_id = current_trace_id()
    if not trace_id:
        return

    with _lock:
        trace = _traces.get(trace_id)
        if not trace:
            return

        trace["status"] = status
        trace["ended_at"] = time.time()
        trace["duration_ms"] = round((trace["ended_at"] - trace["started_at"]) * 1000, 2)
        if metadata:
            trace["metadata"].update(_sanitize_attributes(metadata))


@contextmanager
def trace_span(name: str, attributes: Optional[Dict[str, Any]] = None) -> Iterator[None]:
    trace_id = current_trace_id()
    stack = _span_stack_ctx.get()
    span_id = uuid.uuid4().hex[:16]
    parent_span_id = stack[-1] if stack else None
    span_record = {
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "depth": len(stack),
        "name": name,
        "attributes": _sanitize_attributes(attributes),
        "started_at": time.time(),
        "ended_at": None,
        "duration_ms": None,
        "status": "running",
    }
    stack_token = _span_stack_ctx.set(stack + (span_id,))

    otel_cm = None
    if _otel_tracer is not None:
        otel_cm = _otel_tracer.start_as_current_span(name, attributes=span_record["attributes"])
        otel_cm.__enter__()

    try:
        yield
        span_record["status"] = "ok"
    except Exception as exc:
        span_record["status"] = "error"
        span_record["attributes"]["error"] = str(exc)
        raise
    finally:
        span_record["ended_at"] = time.time()
        span_record["duration_ms"] = round(
            (span_record["ended_at"] - span_record["started_at"]) * 1000, 2
        )
        _span_stack_ctx.reset(stack_token)
        if trace_id:
            with _lock:
                trace = _traces.get(trace_id)
                if trace is not None:
                    trace["spans"].append(span_record)
        if otel_cm is not None:
            otel_cm.__exit__(None, None, None)


def get_trace(trace_id: str) -> Dict[str, Any]:
    with _lock:
        trace = _traces.get(trace_id)
        if not trace:
            return {}
        payload = deepcopy(trace)

    spans = sorted(
        payload["spans"],
        key=lambda item: (item.get("started_at", 0.0), item.get("depth", 0)),
    )
    base_time = payload.get("started_at") or 0.0
    for span in spans:
        started_at = span.get("started_at") or base_time
        ended_at = span.get("ended_at") or started_at
        span["start_offset_ms"] = round((started_at - base_time) * 1000, 2)
        span["end_offset_ms"] = round((ended_at - base_time) * 1000, 2)

    payload["spans"] = spans
    payload["summary"] = {
        "span_count": len(spans),
        "error_count": sum(1 for span in spans if span.get("status") == "error"),
        "total_duration_ms": payload.get("duration_ms"),
        "root_spans": [span["name"] for span in spans if span.get("depth", 0) == 0],
    }
    return payload
