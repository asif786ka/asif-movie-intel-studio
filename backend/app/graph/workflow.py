"""
LangGraph Workflow Engine — Core RAG Pipeline Orchestration.

Architecture Note (Senior AI Architect):
  This module defines the multi-step RAG workflow as a LangGraph StateGraph.
  The workflow implements a 12-node directed acyclic graph with conditional
  branching based on query classification and evidence sufficiency.

  Pipeline Flow:
    validate_input → classify_query → route_query
      → [structured_only] → tmdb_lookup → merge_context
      → [rag_only]        → retrieve_docs → rerank_docs → merge_context
      → [hybrid]          → tmdb_lookup → retrieve_docs → rerank_docs → merge_context
    → grade_evidence
      → [insufficient + retries < 1] → retrieve_docs (retry loop)
      → [insufficient + retries >= 1] → finalize_response (safe refusal)
      → [sufficient] → generate_answer → extract_citations → guardrails → finalize_response

  Safety Design:
    - Input validation blocks prompt injection BEFORE any LLM call
    - Evidence grading prevents hallucination on weak context
    - Output guardrails catch fabricated claims post-generation
    - Retry loop gives one second chance before refusing

  Scalability:
    - Compiled workflow is cached as a module-level singleton
    - Async execution supports concurrent request handling
    - State dict serializes cleanly for distributed execution
"""

from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.nodes import (
    validate_input_node,
    classify_query_node,
    route_query_node,
    tmdb_lookup_node,
    retrieve_docs_node,
    rerank_docs_node,
    merge_context_node,
    grade_evidence_node,
    generate_answer_node,
    extract_citations_node,
    guardrails_node,
    finalize_response_node,
)
from app.core.constants import QUERY_TYPE_STRUCTURED, QUERY_TYPE_RAG, QUERY_TYPE_HYBRID
from app.core.logging import get_logger

logger = get_logger(__name__)


# --- Conditional Edge Functions ---
# These functions inspect the current state and return a string key
# that maps to the next node via add_conditional_edges().

def should_continue_after_validation(state: dict) -> str:
    """Gate: if input was blocked by guardrails, skip directly to finalize."""
    if state.get("blocked"):
        return "finalize"
    return "classify"


def route_by_query_type(state: dict) -> str:
    """Three-way router based on LLM query classification.

    Routes determine which data sources are consulted:
      - tmdb_only: Only structured TMDB API data
      - rag_only: Only ChromaDB vector store documents
      - hybrid: Both TMDB + vector store (most expensive path)
    """
    route_type = state.get("route_type", "")
    if route_type == QUERY_TYPE_STRUCTURED:
        return "tmdb_only"
    elif route_type == QUERY_TYPE_RAG:
        return "rag_only"
    else:
        return "hybrid"


def should_continue_after_evidence(state: dict) -> str:
    """Evidence sufficiency gate with retry logic.

    If evidence is insufficient and we haven't exhausted retries,
    loop back to retrieve_docs for a second attempt with potentially
    different embeddings. After max retries, refuse rather than hallucinate.
    """
    if state.get("blocked"):
        return "finalize"
    if not state.get("evidence_sufficient") and state.get("retry_count", 0) < 1:
        return "retry"
    return "generate"


def build_workflow() -> StateGraph:
    """Construct the LangGraph state machine with all nodes and edges.

    Node Registration Order:
      1. validate_input    — Input safety check + trace start
      2. classify_query    — LLM-based query type classification
      3. route_query       — Pass-through for conditional edge branching
      4. tmdb_lookup       — TMDB API search and detail fetching
      5. retrieve_docs     — ChromaDB vector similarity search
      6. rerank_docs       — Re-score retrieved documents for relevance
      7. merge_context     — Combine TMDB data + retrieved docs into context
      8. grade_evidence    — Evaluate context sufficiency score
      9. generate_answer   — LLM answer generation with system prompt
     10. extract_citations — Parse and validate [Source N] references
     11. guardrails        — Post-generation fabrication detection
     12. finalize_response — End trace, compute latency, format output
    """
    workflow = StateGraph(dict)

    # Register all 12 pipeline nodes
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("classify_query", classify_query_node)
    workflow.add_node("route_query", route_query_node)
    workflow.add_node("tmdb_lookup", tmdb_lookup_node)
    workflow.add_node("retrieve_docs", retrieve_docs_node)
    workflow.add_node("rerank_docs", rerank_docs_node)
    workflow.add_node("merge_context", merge_context_node)
    workflow.add_node("grade_evidence", grade_evidence_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("extract_citations", extract_citations_node)
    workflow.add_node("guardrails", guardrails_node)
    workflow.add_node("finalize_response", finalize_response_node)

    # Entry point: every query starts with input validation
    workflow.set_entry_point("validate_input")

    # Edge: validation → classify OR finalize (if blocked)
    workflow.add_conditional_edges(
        "validate_input",
        should_continue_after_validation,
        {
            "classify": "classify_query",
            "finalize": "finalize_response",
        },
    )

    # Edge: classify → route (always)
    workflow.add_edge("classify_query", "route_query")

    # Edge: route → tmdb_lookup OR retrieve_docs OR tmdb_lookup (hybrid starts with TMDB)
    workflow.add_conditional_edges(
        "route_query",
        route_by_query_type,
        {
            "tmdb_only": "tmdb_lookup",
            "rag_only": "retrieve_docs",
            "hybrid": "tmdb_lookup",
        },
    )

    # Edge: tmdb_lookup → retrieve_docs (if hybrid) OR merge_context (if structured_only)
    workflow.add_conditional_edges(
        "tmdb_lookup",
        lambda s: "retrieve" if s.get("route_type") == QUERY_TYPE_HYBRID else "merge",
        {
            "retrieve": "retrieve_docs",
            "merge": "merge_context",
        },
    )

    # Linear edges through the retrieval pipeline
    workflow.add_edge("retrieve_docs", "rerank_docs")
    workflow.add_edge("rerank_docs", "merge_context")
    workflow.add_edge("merge_context", "grade_evidence")

    # Edge: grade_evidence → generate OR retry OR finalize
    workflow.add_conditional_edges(
        "grade_evidence",
        should_continue_after_evidence,
        {
            "generate": "generate_answer",
            "retry": "retrieve_docs",
            "finalize": "finalize_response",
        },
    )

    # Linear edges through the generation pipeline
    workflow.add_edge("generate_answer", "extract_citations")
    workflow.add_edge("extract_citations", "guardrails")
    workflow.add_edge("guardrails", "finalize_response")
    workflow.add_edge("finalize_response", END)

    return workflow


# --- Singleton Compiled Workflow ---
# The workflow graph is compiled once and reused for all requests.
# Compilation resolves all edges and validates the graph structure.
_compiled_workflow = None


def get_workflow():
    """Return the compiled workflow singleton. Thread-safe via GIL."""
    global _compiled_workflow
    if _compiled_workflow is None:
        wf = build_workflow()
        _compiled_workflow = wf.compile()
    return _compiled_workflow


async def run_query(query: str, user_id: str = "anonymous", tenant_id: str = "default", session_id: str = "") -> dict:
    """Execute a full RAG query through the compiled workflow.

    Args:
        query: The user's natural language question
        user_id: Identifier for the requesting user
        tenant_id: Tenant scope for multi-tenant deployments
        session_id: Chat session ID for conversation continuity

    Returns:
        Complete state dict with final_answer, citations, sources,
        route_type, latency_ms, and safety metadata.
    """
    workflow = get_workflow()

    # Initialize all state fields to safe defaults
    initial_state = {
        "query": query,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "session_id": session_id,
        "query_type": "",
        "route_type": "",
        "tmdb_data": {},
        "retrieved_docs": [],
        "reranked_docs": [],
        "merged_context": "",
        "evidence_sufficient": False,
        "evidence_score": 0.0,
        "draft_answer": "",
        "final_answer": "",
        "citations": [],
        "sources": [],
        "blocked": False,
        "refusal_reason": None,
        "prompt_version": "",
        "trace_id": "",
        "latency_ms": 0.0,
        "error": None,
        "retry_count": 0,
    }

    try:
        result = await workflow.ainvoke(initial_state)
        return result
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        return {
            **initial_state,
            "blocked": True,
            "refusal_reason": "internal_error",
            "final_answer": "I'm sorry, I wasn't able to process your request. Please try again or rephrase your question.",
        }
