from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EvalMetric(BaseModel):
    name: str
    value: float
    description: str = ""
    threshold: Optional[float] = None
    passed: Optional[bool] = None


class EvalResult(BaseModel):
    run_id: str
    timestamp: datetime
    metrics: list[EvalMetric] = []
    total_queries: int = 0
    passed: int = 0
    failed: int = 0
    dataset_name: str = ""


class EvalRunRequest(BaseModel):
    dataset: str = "movie_eval_set"
    max_queries: int = 10
    include_adversarial: bool = False


class MetricsResponse(BaseModel):
    total_queries: int = 0
    total_chunks: int = 0
    avg_citation_count: float = 0.0
    refusal_rate: float = 0.0
    unsupported_claim_rate: float = 0.0
    p95_latency_ms: float = 0.0
    route_distribution: dict[str, int] = {}
    prompt_versions: dict = {}
    last_eval_run: Optional[EvalResult] = None
