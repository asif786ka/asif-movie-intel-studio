from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Citation(BaseModel):
    source_index: int
    source_title: str
    source_type: str = "document"
    chunk_text: str = ""
    relevance_score: float = 0.0
    metadata: dict = {}


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    user_id: str = "anonymous"
    tenant_id: str = "default"
    include_sources: bool = True
    max_sources: int = 5


class ChatResponse(BaseModel):
    answer: str
    query_type: str
    route_type: str
    citations: list[Citation] = []
    sources: list[dict] = []
    trace_id: str = ""
    latency_ms: float = 0.0
    prompt_version: str = ""
    evidence_sufficient: bool = True
    blocked: bool = False
    refusal_reason: Optional[str] = None
    session_id: str = ""


class StreamChunk(BaseModel):
    content: str = ""
    done: bool = False
    metadata: Optional[dict] = None


class ChatHistoryEntry(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    metadata: dict = {}


class ChatSession(BaseModel):
    session_id: str
    messages: list[ChatHistoryEntry] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now())
