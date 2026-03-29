import time
import uuid
from fastapi import APIRouter
from app.models.schemas_eval import EvalRunRequest, MetricsResponse
from app.models.schemas_common import APIResponse
from app.services.eval_service import eval_service
from app.db.metadata_store import metadata_store
from app.db.vector_store import vector_store
from app.core.versioning import get_all_versions
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/run")
async def run_evaluation(request: EvalRunRequest):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    result = await eval_service.run_evaluation(
        dataset_name=request.dataset,
        max_queries=request.max_queries,
    )
    latency = (time.time() - start_time) * 1000
    return APIResponse(success=True, data=result.model_dump(), trace_id=trace_id, latency_ms=latency, route_type="direct")


@router.get("/metrics")
async def get_metrics():
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    stored_metrics = metadata_store.get_metrics()
    latest_eval = eval_service.get_latest_result()

    response = MetricsResponse(
        total_queries=stored_metrics["total_queries"],
        total_chunks=vector_store.count(),
        avg_citation_count=stored_metrics["avg_citation_count"],
        refusal_rate=stored_metrics["refusal_rate"],
        unsupported_claim_rate=stored_metrics["unsupported_claim_rate"],
        p95_latency_ms=stored_metrics["p95_latency_ms"],
        route_distribution=stored_metrics["route_distribution"],
        prompt_versions=get_all_versions(),
        last_eval_run=latest_eval,
    )
    latency = (time.time() - start_time) * 1000
    return APIResponse(success=True, data=response.model_dump(), trace_id=trace_id, latency_ms=latency, route_type="direct")
