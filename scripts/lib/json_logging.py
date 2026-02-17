import json
import sys
import time
from typing import Any, Dict, Optional


def _now_ms() -> int:
    return int(time.time() * 1000)


def log_json(
    level: str,
    message: str,
    *,
    event_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    reason: Optional[str] = None,
    error_code: Optional[str] = None,
    duration_ms: Optional[int] = None,
    actor: Optional[str] = None,
    workspace: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    payload = {
        "timestamp": _now_ms(),
        "level": level,
        "message": message,
        "event_id": event_id,
        "trace_id": trace_id,
        "workflow_id": workflow_id,
        "source": source,
        "status": status,
        "reason": reason,
        "error_code": error_code,
        "duration_ms": duration_ms,
        "actor": actor,
        "workspace": workspace,
        "extra": extra or {},
    }
    # OTel Trace Injection (Optional)
    if not trace_id:
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            if span.get_span_context().is_valid:
                trace_id = format(span.get_span_context().trace_id, "032x")
                if "trace_id" not in payload: 
                     payload["trace_id"] = trace_id
        except ImportError:
            pass

    print(json.dumps(payload), file=sys.stderr, flush=True)
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer("windmill_automation")
        with tracer.start_as_current_span("log_json") as span:
            if trace_id:
                span.set_attribute("trace_id", trace_id)
            if event_id:
                span.set_attribute("event_id", event_id)
            span.set_attribute("level", level)
            span.set_attribute("message", message)
    except Exception:
        pass
