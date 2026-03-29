from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class APIResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None
    latency_ms: Optional[float] = None
    prompt_version: Optional[str] = None
    route_type: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class AuditEntry(BaseModel):
    event_type: str
    user_id: str = "anonymous"
    tenant_id: str = "default"
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    details: dict[str, Any] = {}
