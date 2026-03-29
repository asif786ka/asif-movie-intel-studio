from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class IngestionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    movie_title: Optional[str] = None
    source_type: str = "document"
    source_url: Optional[str] = None
    release_year: Optional[int] = None
    actor: Optional[str] = None
    director: Optional[str] = None
    franchise: Optional[str] = None
    tmdb_id: Optional[int] = None
    tenant_id: str = "default"


class UploadResponse(BaseModel):
    job_id: str
    filename: str
    status: IngestionStatus = IngestionStatus.PENDING
    message: str = ""
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class UploadStatusResponse(BaseModel):
    job_id: str
    filename: str
    status: IngestionStatus
    chunk_count: int = 0
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    completed_at: Optional[datetime] = None


class BulkUploadResponse(BaseModel):
    jobs: list[UploadResponse] = []
    total_files: int = 0
    accepted: int = 0
    rejected: int = 0
    errors: list[str] = []
