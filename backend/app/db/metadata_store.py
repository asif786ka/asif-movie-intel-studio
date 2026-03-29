from typing import Optional
from datetime import datetime
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger(__name__)


class MetadataStore:
    def __init__(self):
        self.upload_jobs: dict[str, dict] = {}
        self.chat_sessions: dict[str, list[dict]] = defaultdict(list)
        self.query_logs: list[dict] = []
        self.metrics: dict[str, float] = {
            "total_queries": 0,
            "total_refusals": 0,
            "total_citations": 0,
            "total_unsupported_claims": 0,
        }
        self.route_counts: dict[str, int] = defaultdict(int)
        self.latencies: list[float] = []

    def add_upload_job(self, job_id: str, filename: str, status: str = "pending"):
        self.upload_jobs[job_id] = {
            "job_id": job_id,
            "filename": filename,
            "status": status,
            "chunk_count": 0,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
        }

    def update_upload_job(self, job_id: str, **kwargs):
        if job_id in self.upload_jobs:
            self.upload_jobs[job_id].update(kwargs)

    def get_upload_job(self, job_id: str) -> Optional[dict]:
        return self.upload_jobs.get(job_id)

    def add_chat_message(self, session_id: str, role: str, content: str, metadata: dict | None = None):
        self.chat_sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })

    def get_chat_history(self, session_id: str) -> list[dict]:
        return self.chat_sessions.get(session_id, [])

    def log_query(self, query: str, route_type: str, latency_ms: float, citation_count: int, refused: bool = False):
        self.query_logs.append({
            "query": query,
            "route_type": route_type,
            "latency_ms": latency_ms,
            "citation_count": citation_count,
            "refused": refused,
            "timestamp": datetime.now().isoformat(),
        })
        self.metrics["total_queries"] += 1
        self.metrics["total_citations"] += citation_count
        if refused:
            self.metrics["total_refusals"] += 1
        self.route_counts[route_type] += 1
        self.latencies.append(latency_ms)

    def get_metrics(self) -> dict:
        total = self.metrics["total_queries"]
        return {
            "total_queries": int(total),
            "total_chunks": 0,
            "avg_citation_count": self.metrics["total_citations"] / max(total, 1),
            "refusal_rate": self.metrics["total_refusals"] / max(total, 1),
            "unsupported_claim_rate": self.metrics["total_unsupported_claims"] / max(total, 1),
            "p95_latency_ms": sorted(self.latencies)[int(len(self.latencies) * 0.95)] if self.latencies else 0.0,
            "route_distribution": dict(self.route_counts),
        }


metadata_store = MetadataStore()
