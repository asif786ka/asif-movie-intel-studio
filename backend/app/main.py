"""
Asif Movie Intel Studio — FastAPI Application Entry Point.

Architecture Note (Senior AI Architect):
  This is the main application bootstrap that wires together:
    1. FastAPI app with CORS, rate limiting, and timing middleware
    2. Route handlers for chat, movies, upload, eval, and health endpoints
    3. Observability setup (LangSmith tracing + OpenTelemetry)
    4. Startup hooks for data seeding and initialization

  Request Flow:
    Client → CORS middleware → Rate limiter → Timing middleware → Router → Handler

  The api-server (Express/Node.js) proxies /api/* requests to this backend
  in development. In production Docker, Nginx handles the proxying.
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import traceback

from app.core.config import settings
from app.core.logging import get_logger
from app.core.versioning import get_all_versions
from app.core.security import rate_limiter
from app.observability.langsmith_setup import setup_langsmith
from app.observability.otel_setup import setup_opentelemetry
from app.api.routes_health import router as health_router
from app.api.routes_chat import router as chat_router
from app.api.routes_upload import router as upload_router
from app.api.routes_movies import router as movies_router
from app.api.routes_eval import router as eval_router

logger = get_logger(__name__)

# --- FastAPI Application Instance ---
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A hybrid movie intel platform combining TMDB structured data with RAG over unstructured movie documents",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# --- CORS Configuration ---
# In development, allow all origins. In production, restrict to your domain.
origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Observability Setup ---
# LangSmith: Distributed tracing for LLM calls and chain execution
# OpenTelemetry: Standard observability for HTTP requests and spans
setup_langsmith()
setup_opentelemetry(app)


# --- Global Middleware: Timing + Rate Limiting ---
@app.middleware("http")
async def add_timing_and_rate_limit(request: Request, call_next):
    """Middleware that adds response timing headers and enforces rate limits.

    Rate limiting applies to /api/chat and /api/upload endpoints to prevent
    abuse. All responses include X-Response-Time-Ms for performance monitoring.
    """
    start = time.time()
    try:
        # Apply rate limiting to chat and upload endpoints
        if request.url.path.startswith("/api/chat") or request.url.path.startswith("/api/upload"):
            client_ip = request.client.host if request.client else "unknown"
            if not rate_limiter.check(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={"success": False, "error": "Rate limit exceeded. Please try again later."},
                )
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        response.headers["X-Response-Time-Ms"] = f"{duration:.2f}"
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"},
        )


# --- Route Registration ---
# All routes are prefixed with /api to support the Express proxy architecture
app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(movies_router, prefix="/api")
app.include_router(eval_router, prefix="/api")


# --- Startup Hook ---
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup.

    Seeds the ChromaDB vector store with sample documents if empty.
    Seeding runs in the background so the server can start accepting
    requests immediately (important for production health checks).
    """
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"TMDB configured: {bool(settings.tmdb_api_key)}")
    logger.info(f"Versions: {get_all_versions()}")

    async def _seed_in_background():
        try:
            from app.scripts.seed_data import seed_sample_documents
            await seed_sample_documents()
        except Exception as e:
            logger.error(f"Background seeding failed: {e}")

    asyncio.create_task(_seed_in_background())


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", settings.backend_port))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
