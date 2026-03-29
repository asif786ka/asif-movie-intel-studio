"""
GraphState — Immutable state schema for the LangGraph RAG workflow.

Architecture Note (Senior AI Architect):
  The GraphState acts as the single source of truth flowing through every node
  in the LangGraph state machine. Each node receives the full state, performs its
  operation, and returns a new (merged) state dict. This pattern enables:

  1. Full traceability — every field is available at every step for debugging
  2. Conditional routing — route_type, blocked, evidence_sufficient drive edges
  3. Retry semantics — retry_count tracks re-retrieval attempts
  4. Guardrail enforcement — blocked + refusal_reason short-circuit the pipeline

  Scalability: Since state is a dict (not a class instance), it serializes
  trivially for distributed execution (e.g., Celery, LangGraph Cloud).
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


class GraphState(BaseModel):
    """
    Pydantic model defining the complete state schema for the RAG workflow.

    Fields are grouped by lifecycle stage:
      - Identity: query, user_id, tenant_id, session_id
      - Classification: query_type, route_type
      - Retrieval: tmdb_data, retrieved_docs, reranked_docs, merged_context
      - Evidence: evidence_sufficient, evidence_score
      - Generation: draft_answer, final_answer, citations, sources
      - Safety: blocked, refusal_reason
      - Observability: prompt_version, trace_id, latency_ms
      - Error handling: error, retry_count
    """

    # --- Identity & Input ---
    query: str = ""
    user_id: str = "anonymous"
    tenant_id: str = "default"
    session_id: str = ""

    # --- Query Classification (set by classify_query_node) ---
    query_type: str = ""       # Raw LLM classification output
    route_type: str = ""       # Normalized route: structured_only | rag_only | hybrid

    # --- Data Retrieval (populated by tmdb_lookup, retrieve_docs, rerank_docs) ---
    tmdb_data: dict[str, Any] = {}       # Structured movie data from TMDB API
    retrieved_docs: list[dict] = []      # Raw vector store results
    reranked_docs: list[dict] = []       # Relevance-scored documents after reranking
    merged_context: str = ""             # Final context string fed to the LLM

    # --- Evidence Grading (set by grade_evidence_node) ---
    evidence_sufficient: bool = False    # Whether context passes sufficiency threshold
    evidence_score: float = 0.0          # Numeric score (0.0-1.0)

    # --- Answer Generation & Citations ---
    draft_answer: str = ""               # Raw LLM output before guardrail check
    final_answer: str = ""               # Verified answer returned to user
    citations: list[dict] = []           # Extracted [Source N] references
    sources: list[dict] = []             # Source document snippets for citation display

    # --- Safety & Guardrails ---
    blocked: bool = False                # If True, pipeline short-circuits to finalize
    refusal_reason: Optional[str] = None # Human-readable reason for blocking

    # --- Observability & Versioning ---
    prompt_version: str = ""             # Tracks which prompt version was used
    trace_id: str = ""                   # Unique ID for end-to-end request tracing
    latency_ms: float = 0.0             # Total pipeline execution time

    # --- Error Handling ---
    error: Optional[str] = None          # Error message if pipeline fails
    retry_count: int = 0                 # Number of retrieval retry attempts

    model_config = {"arbitrary_types_allowed": True}
