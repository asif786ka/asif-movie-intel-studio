import uuid
import os
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.models.schemas_upload import UploadResponse, UploadStatusResponse, BulkUploadResponse, DocumentMetadata, IngestionStatus
from app.models.schemas_common import APIResponse
from app.services.ingestion_service import ingestion_service
from app.core.security import validate_file_upload
from app.core.config import settings
from app.db.metadata_store import metadata_store
from app.db.audit_store import audit_store
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    movie_title: Optional[str] = Form(None),
    source_type: str = Form("document"),
    director: Optional[str] = Form(None),
    franchise: Optional[str] = Form(None),
    release_year: Optional[int] = Form(None),
    tmdb_id: Optional[int] = Form(None),
    tenant_id: str = Form("default"),
):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]

    content = await file.read()
    is_valid, error = validate_file_upload(file.filename or "", len(content), settings.max_upload_size_mb)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    metadata = DocumentMetadata(
        movie_title=movie_title,
        source_type=source_type,
        director=director,
        franchise=franchise,
        release_year=release_year,
        tmdb_id=tmdb_id,
        tenant_id=tenant_id,
    )

    from app.services.file_parser_service import extract_text_from_file
    text_content = extract_text_from_file(content, file.filename or "unknown")
    if not text_content or not text_content.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the uploaded file. For images, ensure they contain readable text.")

    job_id = await ingestion_service.ingest_document(text_content, file.filename or "unknown", metadata)

    job = metadata_store.get_upload_job(job_id) or {}
    latency = (time.time() - start_time) * 1000
    response = UploadResponse(
        job_id=job_id,
        filename=file.filename or "unknown",
        status=IngestionStatus(job.get("status", "pending")),
        message=f"Document ingested successfully with {job.get('chunk_count', 0)} chunks",
        chunk_count=job.get("chunk_count", 0),
    )

    return APIResponse(success=True, data=response.model_dump(), trace_id=trace_id, latency_ms=latency, route_type="direct")


@router.post("/bulk")
async def upload_bulk(
    files: list[UploadFile] = File(...),
    movie_title: Optional[str] = Form(None),
    source_type: str = Form("document"),
    tenant_id: str = Form("default"),
):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]

    jobs = []
    errors = []
    accepted = 0
    rejected = 0

    for file in files:
        content = await file.read()
        is_valid, error = validate_file_upload(file.filename or "", len(content), settings.max_upload_size_mb)
        if not is_valid:
            errors.append(f"{file.filename}: {error}")
            rejected += 1
            continue

        from app.services.file_parser_service import extract_text_from_file
        metadata = DocumentMetadata(movie_title=movie_title, source_type=source_type, tenant_id=tenant_id)
        text_content = extract_text_from_file(content, file.filename or "unknown")
        if not text_content or not text_content.strip():
            errors.append(f"{file.filename}: Could not extract text")
            rejected += 1
            continue
        job_id = await ingestion_service.ingest_document(text_content, file.filename or "unknown", metadata)
        job = metadata_store.get_upload_job(job_id) or {}

        jobs.append(UploadResponse(
            job_id=job_id,
            filename=file.filename or "unknown",
            status=IngestionStatus(job.get("status", "pending")),
            chunk_count=job.get("chunk_count", 0),
        ))
        accepted += 1

    latency = (time.time() - start_time) * 1000
    response = BulkUploadResponse(
        jobs=jobs, total_files=len(files), accepted=accepted, rejected=rejected, errors=errors
    )
    return APIResponse(success=True, data=response.model_dump(), trace_id=trace_id, latency_ms=latency, route_type="direct")


@router.get("/status/{job_id}")
async def get_upload_status(job_id: str):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:12]

    job = metadata_store.get_upload_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    latency = (time.time() - start_time) * 1000
    response = UploadStatusResponse(
        job_id=job["job_id"],
        filename=job["filename"],
        status=IngestionStatus(job["status"]),
        chunk_count=job.get("chunk_count", 0),
        error=job.get("error"),
    )
    return APIResponse(success=True, data=response.model_dump(), trace_id=trace_id, latency_ms=latency, route_type="direct")
