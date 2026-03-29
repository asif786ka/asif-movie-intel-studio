import uuid
import time
from typing import Optional, Any
from contextlib import contextmanager
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TracingService:
    def __init__(self):
        self.traces: dict[str, dict] = {}
        self._langsmith_enabled = settings.langsmith_tracing_enabled

    def start_trace(self, trace_id: Optional[str] = None) -> str:
        trace_id = trace_id or str(uuid.uuid4())[:12]
        self.traces[trace_id] = {
            "trace_id": trace_id,
            "start_time": time.time(),
            "spans": [],
            "metadata": {},
        }
        return trace_id

    def add_span(self, trace_id: str, span_name: str, duration_ms: float, metadata: dict | None = None):
        if trace_id in self.traces:
            self.traces[trace_id]["spans"].append({
                "name": span_name,
                "duration_ms": duration_ms,
                "metadata": metadata or {},
                "timestamp": time.time(),
            })

    def end_trace(self, trace_id: str) -> Optional[dict]:
        if trace_id not in self.traces:
            return None
        trace = self.traces[trace_id]
        trace["end_time"] = time.time()
        trace["total_duration_ms"] = (trace["end_time"] - trace["start_time"]) * 1000
        return trace

    def get_trace(self, trace_id: str) -> Optional[dict]:
        return self.traces.get(trace_id)

    @contextmanager
    def span(self, trace_id: str, span_name: str):
        start = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start) * 1000
            self.add_span(trace_id, span_name, duration)

    def get_recent_traces(self, limit: int = 20) -> list[dict]:
        sorted_traces = sorted(
            self.traces.values(),
            key=lambda t: t.get("start_time", 0),
            reverse=True,
        )
        return sorted_traces[:limit]


tracing_service = TracingService()
