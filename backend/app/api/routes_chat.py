import uuid
import time
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas_chat import ChatRequest, ChatResponse
from app.models.schemas_common import APIResponse
from app.graph.workflow import run_query
from app.services.bedrock_service import llm_provider
from app.services.tracing_service import tracing_service
from app.db.metadata_store import metadata_store
from app.db.audit_store import audit_store
from app.core.versioning import PROMPT_VERSIONS
from app.core.prompts import SYSTEM_PROMPT, ANSWER_GENERATION_PROMPT
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query")
async def chat_query(request: ChatRequest):
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())[:12]

    audit_store.log("chat_query", user_id=request.user_id, tenant_id=request.tenant_id,
                    details={"query": request.query, "session_id": session_id})

    result = await run_query(
        query=request.query,
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        session_id=session_id,
    )

    latency = (time.time() - start_time) * 1000

    metadata_store.add_chat_message(session_id, "user", request.query)
    metadata_store.add_chat_message(session_id, "assistant", result.get("final_answer", ""),
                                    metadata={"trace_id": result.get("trace_id", "")})

    citations = result.get("citations", [])
    metadata_store.log_query(
        query=request.query,
        route_type=result.get("route_type", "unknown"),
        latency_ms=latency,
        citation_count=len(citations),
        refused=result.get("blocked", False),
    )

    response = ChatResponse(
        answer=result.get("final_answer", ""),
        query_type=result.get("query_type", ""),
        route_type=result.get("route_type", ""),
        citations=citations,
        sources=result.get("sources", [])[:request.max_sources] if request.include_sources else [],
        trace_id=result.get("trace_id", ""),
        latency_ms=latency,
        prompt_version=PROMPT_VERSIONS.system_prompt,
        evidence_sufficient=result.get("evidence_sufficient", False),
        blocked=result.get("blocked", False),
        refusal_reason=result.get("refusal_reason"),
        session_id=session_id,
    )

    return APIResponse(success=True, data=response.model_dump(), trace_id=result.get("trace_id", ""), latency_ms=latency, route_type=result.get("route_type", "unknown"))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())[:12]
    trace_id = tracing_service.start_trace()

    async def event_generator():
        start_time = time.time()
        yield f"data: {json.dumps({'type': 'start', 'trace_id': trace_id, 'session_id': session_id})}\n\n"

        result = await run_query(
            query=request.query,
            user_id=request.user_id,
            tenant_id=request.tenant_id,
            session_id=session_id,
        )

        answer = result.get("final_answer", "")
        words = answer.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

        latency_ms = (time.time() - start_time) * 1000
        yield f"data: {json.dumps({'type': 'metadata', 'query_type': result.get('query_type', ''), 'route_type': result.get('route_type', ''), 'citations': result.get('citations', []), 'evidence_sufficient': result.get('evidence_sufficient', False), 'blocked': result.get('blocked', False), 'trace_id': trace_id, 'latency_ms': round(latency_ms, 2)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]
    history = metadata_store.get_chat_history(session_id)
    latency = (time.time() - start_time) * 1000
    return APIResponse(
        success=True,
        data={"session_id": session_id, "messages": history},
        trace_id=trace_id,
        latency_ms=latency,
        route_type="direct",
    )
