import time
import uuid
from fastapi import APIRouter
from app.core.config import settings
from app.core.versioning import get_all_versions
from app.db.vector_store import vector_store
from app.models.schemas_common import APIResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    latency = (time.time() - start_time) * 1000
    return APIResponse(
        success=True,
        data={
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
        },
        trace_id=trace_id,
        latency_ms=latency,
        route_type="direct",
    )


@router.get("/ready")
async def readiness_check():
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    chunk_count = vector_store.count()
    latency = (time.time() - start_time) * 1000
    return APIResponse(
        success=True,
        data={
            "status": "ready",
            "vector_store_chunks": chunk_count,
            "versions": get_all_versions(),
            "llm_provider": settings.llm_provider,
            "tmdb_configured": bool(settings.tmdb_api_key),
        },
        trace_id=trace_id,
        latency_ms=latency,
        route_type="direct",
    )
