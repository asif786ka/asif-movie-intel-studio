import time
import uuid
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas_movie import CompareRequest
from app.models.schemas_common import APIResponse
from app.services.tmdb_service import tmdb_service
from app.services.compare_service import compare_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/search")
async def search_movies(query: str = Query(..., min_length=1), page: int = Query(1, ge=1)):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    results = await tmdb_service.search_movie(query, page)
    latency = (time.time() - start_time) * 1000
    return APIResponse(
        success=True,
        data=[r.model_dump() for r in results],
        trace_id=trace_id,
        latency_ms=latency,
        route_type="direct",
    )


@router.get("/{movie_id}")
async def get_movie_details(movie_id: int):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    details = await tmdb_service.get_movie_details(movie_id)
    if not details:
        raise HTTPException(status_code=404, detail="Movie not found")
    latency = (time.time() - start_time) * 1000
    return APIResponse(success=True, data=details.model_dump(), trace_id=trace_id, latency_ms=latency, route_type="direct")


@router.get("/{movie_id}/credits")
async def get_movie_credits(movie_id: int):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    credits = await tmdb_service.get_movie_credits(movie_id)
    if not credits:
        raise HTTPException(status_code=404, detail="Credits not found")
    latency = (time.time() - start_time) * 1000
    return APIResponse(success=True, data=credits.model_dump(), trace_id=trace_id, latency_ms=latency, route_type="direct")


@router.get("/{movie_id}/similar")
async def get_similar_movies(movie_id: int):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    results = await tmdb_service.get_similar_movies(movie_id)
    latency = (time.time() - start_time) * 1000
    return APIResponse(
        success=True,
        data=[r.model_dump() for r in results],
        trace_id=trace_id,
        latency_ms=latency,
        route_type="direct",
    )


@router.get("/{movie_id}/brief")
async def get_movie_brief(movie_id: int):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    brief = await tmdb_service.get_movie_brief(movie_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Movie not found")
    latency = (time.time() - start_time) * 1000
    return APIResponse(success=True, data=brief.model_dump(), trace_id=trace_id, latency_ms=latency, route_type="direct")


@router.post("/compare")
async def compare_movies(request: CompareRequest):
    start_time = time.time()
    result = await compare_service.compare_movies(request.movie_ids, request.dimensions)
    latency = (time.time() - start_time) * 1000
    return APIResponse(
        success=True,
        data=result.model_dump(),
        trace_id=result.trace_id,
        latency_ms=latency,
        route_type="hybrid",
    )
