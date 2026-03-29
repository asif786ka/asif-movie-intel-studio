"""
LangGraph Pipeline Nodes — Individual processing steps in the RAG workflow.

Architecture Note (Senior AI Architect):
  Each node is an async function that receives the full GraphState dict,
  performs one atomic operation, and returns a merged state dict.

  Node Design Principles:
    1. Single Responsibility — each node does exactly one thing
    2. Fail-Safe — every node checks state.blocked and short-circuits
    3. Observable — every node wraps its work in a tracing span
    4. Immutable State — nodes return {**state, ...} instead of mutating

  Safety & Guardrails:
    - validate_input_node: Prompt injection detection (regex + heuristic)
    - grade_evidence_node: Prevents hallucination on insufficient context
    - guardrails_node: Post-generation fabrication detection
    - generate_answer_node: Enforces max retries before safe refusal

  The node ordering and conditional edges are defined in workflow.py.
"""

import time
import re
from app.core.logging import get_logger
from app.core.prompts import (
    SYSTEM_PROMPT, QUERY_CLASSIFIER_PROMPT,
    ANSWER_GENERATION_PROMPT, EVIDENCE_GRADING_PROMPT,
)
from app.core.constants import (
    QUERY_TYPE_STRUCTURED, QUERY_TYPE_RAG, QUERY_TYPE_HYBRID,
    SAFE_REFUSAL_MESSAGE, MAX_RETRIES_EVIDENCE,
)
from app.core.versioning import PROMPT_VERSIONS
from app.graph.state import GraphState
from app.services.bedrock_service import llm_provider
from app.services.tmdb_service import tmdb_service
from app.services.retrieval_service import retrieval_service, RetrievedDocument
from app.services.rerank_service import rerank_service
from app.services.citation_service import citation_service
from app.services.guardrail_service import guardrail_service
from app.services.tracing_service import tracing_service

logger = get_logger(__name__)


# ============================================================================
# NODE 1: INPUT VALIDATION
# First line of defense — blocks prompt injection before any LLM call.
# ============================================================================

async def validate_input_node(state: dict) -> dict:
    """Validate user input for safety and minimum quality.

    Security: Runs prompt injection detection patterns against the query.
    If injection is detected, sets blocked=True and the pipeline short-circuits
    to finalize_response without ever calling the LLM.
    """
    query = state.get("query", "")

    # Reject empty or trivially short queries
    if not query or len(query.strip()) < 2:
        return {**state, "blocked": True, "refusal_reason": "Query too short or empty."}

    # Run prompt injection detection (regex patterns + heuristics)
    is_safe, reason = await guardrail_service.check_input(query)
    if not is_safe:
        return {**state, "blocked": True, "refusal_reason": reason}

    # Start a new trace for this request (for observability)
    trace_id = tracing_service.start_trace()
    return {**state, "trace_id": trace_id, "prompt_version": PROMPT_VERSIONS.system_prompt}


# ============================================================================
# NODE 2: QUERY CLASSIFICATION
# LLM-based routing decision with keyword fallback heuristics.
# ============================================================================

async def classify_query_node(state: dict) -> dict:
    """Classify the user query into structured_only, rag_only, or hybrid.

    Uses the LLM with temperature=0 for deterministic classification.
    Falls back to keyword-based heuristics if LLM returns unexpected output.

    Routing Impact:
      - structured_only → only TMDB API (cheapest, fastest)
      - rag_only → only vector store retrieval (document analysis)
      - hybrid → both sources (most comprehensive, most expensive)
    """
    if state.get("blocked"):
        return state
    query = state["query"]
    trace_id = state.get("trace_id", "")

    with tracing_service.span(trace_id, "classify_query"):
        prompt = QUERY_CLASSIFIER_PROMPT.format(query=query)
        classification = await llm_provider.generate(prompt, temperature=0.0, max_tokens=20)
        classification = classification.strip().lower()

        # Fallback heuristics when LLM returns unexpected classification
        if classification not in [QUERY_TYPE_STRUCTURED, QUERY_TYPE_RAG, QUERY_TYPE_HYBRID]:
            if any(w in query.lower() for w in ["compare", "versus", "vs", "contrast", "both"]):
                classification = QUERY_TYPE_HYBRID
            elif any(w in query.lower() for w in ["theme", "review", "analysis", "explain", "summarize", "recurring", "philosophy"]):
                classification = QUERY_TYPE_RAG
            else:
                classification = QUERY_TYPE_STRUCTURED

    return {**state, "query_type": classification, "route_type": classification}


# ============================================================================
# NODE 3: ROUTE QUERY (pass-through for conditional edge branching)
# ============================================================================

async def route_query_node(state: dict) -> dict:
    """Pass-through node that enables conditional edge branching in LangGraph.

    The actual routing logic lives in workflow.py's route_by_query_type().
    This node exists because LangGraph requires a node at the source of
    conditional edges.
    """
    return state


# ============================================================================
# NODE 4: TMDB LOOKUP
# Structured data retrieval from The Movie Database API.
# ============================================================================

async def tmdb_lookup_node(state: dict) -> dict:
    """Search TMDB API for movie data and fetch details + credits.

    Falls back to seed data when TMDB_API_KEY is not configured,
    ensuring the demo works without any external API keys.

    Data Retrieved: title, release_date, rating, overview, genres,
    runtime, budget, revenue, cast (top 5), directors.
    """
    if state.get("blocked"):
        return state
    query = state["query"]
    trace_id = state.get("trace_id", "")

    with tracing_service.span(trace_id, "tmdb_lookup"):
        results = await tmdb_service.search_movie(query)
        tmdb_data = {}
        if results:
            top_movie = results[0]
            details = await tmdb_service.get_movie_details(top_movie.id)
            credits = await tmdb_service.get_movie_credits(top_movie.id)
            tmdb_data = {
                "search_results": [r.model_dump() for r in results[:5]],
                "top_movie": details.model_dump() if details else {},
                "credits": credits.model_dump() if credits else {},
            }

    return {**state, "tmdb_data": tmdb_data}


# ============================================================================
# NODE 5: DOCUMENT RETRIEVAL
# Vector similarity search against ChromaDB.
# ============================================================================

async def retrieve_docs_node(state: dict) -> dict:
    """Retrieve relevant documents from ChromaDB vector store.

    Uses embedding_service to convert query to vector, then performs
    cosine similarity search. Supports retry: if this is a second attempt,
    retry_count is incremented to track the retry loop.
    """
    if state.get("blocked"):
        return state
    query = state["query"]
    trace_id = state.get("trace_id", "")
    retry_count = state.get("retry_count", 0) + (1 if state.get("retrieved_docs") else 0)

    with tracing_service.span(trace_id, "retrieve_docs"):
        docs = await retrieval_service.retrieve(query, top_k=10)
        retrieved = [d.to_dict() for d in docs]

    return {**state, "retrieved_docs": retrieved, "retry_count": retry_count}


# ============================================================================
# NODE 6: DOCUMENT RERANKING
# Re-score retrieved documents for query-specific relevance.
# ============================================================================

async def rerank_docs_node(state: dict) -> dict:
    """Re-rank retrieved documents by relevance to the specific query.

    Reranking improves precision by re-scoring documents that were
    retrieved via embedding similarity (which optimizes for recall).
    """
    if state.get("blocked"):
        return state
    query = state["query"]
    trace_id = state.get("trace_id", "")
    retrieved = state.get("retrieved_docs", [])

    with tracing_service.span(trace_id, "rerank_docs"):
        docs = [RetrievedDocument(**d) for d in retrieved]
        reranked = await rerank_service.rerank(query, docs)
        reranked_dicts = [d.to_dict() for d in reranked]

    return {**state, "reranked_docs": reranked_dicts}


# ============================================================================
# NODE 7: CONTEXT MERGING
# Combines TMDB structured data with reranked documents into a single context.
# ============================================================================

async def merge_context_node(state: dict) -> dict:
    """Merge TMDB data and/or retrieved documents into a unified context string.

    The merged context is what gets fed to the LLM for answer generation.
    Sources are numbered [Source 1], [Source 2], etc. for citation tracking.

    Context Layout:
      - TMDB DATA section (if structured_only or hybrid)
      - [Source N] sections for each reranked document (if rag_only or hybrid)
    """
    if state.get("blocked"):
        return state
    tmdb_data = state.get("tmdb_data", {})
    reranked = state.get("reranked_docs", [])
    route_type = state.get("route_type", "")

    context_parts = []

    # Add structured TMDB data for structured_only and hybrid routes
    if route_type in [QUERY_TYPE_STRUCTURED, QUERY_TYPE_HYBRID] and tmdb_data:
        top_movie = tmdb_data.get("top_movie", {})
        if top_movie:
            context_parts.append(
                f"TMDB DATA:\nTitle: {top_movie.get('title', 'N/A')}\n"
                f"Release: {top_movie.get('release_date', 'N/A')}\n"
                f"Rating: {top_movie.get('vote_average', 'N/A')}/10 ({top_movie.get('vote_count', 0)} votes)\n"
                f"Overview: {top_movie.get('overview', 'N/A')}\n"
                f"Genres: {', '.join(g.get('name', '') for g in top_movie.get('genres', []))}\n"
                f"Runtime: {top_movie.get('runtime', 'N/A')} min\n"
                f"Budget: ${top_movie.get('budget', 0):,}\n"
                f"Revenue: ${top_movie.get('revenue', 0):,}"
            )
        credits = tmdb_data.get("credits", {})
        if credits:
            cast = credits.get("cast", [])[:5]
            crew = credits.get("crew", [])
            directors = [c["name"] for c in crew if c.get("job") == "Director"]
            if directors:
                context_parts.append(f"Director(s): {', '.join(directors)}")
            if cast:
                cast_str = ", ".join([f"{c['name']} as {c.get('character', 'N/A')}" for c in cast])
                context_parts.append(f"Top Cast: {cast_str}")

    # Add retrieved document sources for rag_only and hybrid routes
    if route_type in [QUERY_TYPE_RAG, QUERY_TYPE_HYBRID] and reranked:
        for i, doc in enumerate(reranked):
            source_type = doc.get("metadata", {}).get("source_type", "document")
            movie_title = doc.get("metadata", {}).get("movie_title", "Unknown")
            context_parts.append(
                f"[Source {i+1}] ({source_type} - {movie_title}):\n{doc['content']}"
            )

    merged = "\n\n".join(context_parts)
    return {**state, "merged_context": merged}


# ============================================================================
# NODE 8: EVIDENCE GRADING
# Evaluates whether retrieved context is sufficient to answer the query.
# ============================================================================

async def grade_evidence_node(state: dict) -> dict:
    """Grade the sufficiency of retrieved evidence for answering the query.

    Safety: This is a critical guardrail. If the context doesn't contain
    enough relevant information, the pipeline either retries retrieval
    or refuses to answer rather than hallucinating.

    Score Ranges:
      - 0.0-0.3: Insufficient → triggers retry or refusal
      - 0.3-0.6: Partial → answer generated with caveats
      - 0.6-1.0: Sufficient → full grounded answer
    """
    if state.get("blocked"):
        return state
    query = state["query"]
    context = state.get("merged_context", "")
    trace_id = state.get("trace_id", "")

    with tracing_service.span(trace_id, "grade_evidence"):
        is_sufficient, score = await guardrail_service.check_evidence_sufficiency(query, context)

    return {**state, "evidence_sufficient": is_sufficient, "evidence_score": score}


# ============================================================================
# NODE 9: ANSWER GENERATION
# LLM generates a grounded answer from the merged context.
# ============================================================================

async def generate_answer_node(state: dict) -> dict:
    """Generate a grounded answer using the LLM with merged context.

    The system prompt enforces citation rules and anti-hallucination policies.
    If evidence retries are exhausted and evidence is still insufficient,
    returns a safe refusal message instead of generating.
    """
    if state.get("blocked"):
        return state

    # Final check: if evidence is still insufficient after max retries, refuse
    if not state.get("evidence_sufficient") and state.get("retry_count", 0) >= MAX_RETRIES_EVIDENCE:
        return {
            **state,
            "blocked": True,
            "refusal_reason": SAFE_REFUSAL_MESSAGE,
            "final_answer": SAFE_REFUSAL_MESSAGE,
        }

    query = state["query"]
    context = state.get("merged_context", "")
    trace_id = state.get("trace_id", "")

    with tracing_service.span(trace_id, "generate_answer"):
        prompt = ANSWER_GENERATION_PROMPT.format(context=context, query=query)
        answer = await llm_provider.generate(prompt, system_prompt=SYSTEM_PROMPT)

    return {**state, "draft_answer": answer}


# ============================================================================
# NODE 10: CITATION EXTRACTION
# Parses [Source N] references and links them to actual source documents.
# ============================================================================

async def extract_citations_node(state: dict) -> dict:
    """Extract and validate [Source N] citations from the generated answer.

    Ensures every citation reference points to a real source document.
    Also adds missing citations where the answer clearly references
    source material without explicit [Source N] tags.
    """
    if state.get("blocked"):
        return state
    answer = state.get("draft_answer", "")
    reranked = state.get("reranked_docs", [])

    sources = [RetrievedDocument(**d) for d in reranked]
    answer = citation_service.add_missing_citations(answer, sources)
    citations = citation_service.extract_citations(answer, sources)

    return {
        **state,
        "draft_answer": answer,
        "citations": [c.model_dump() for c in citations],
        "sources": [{"content": d.content[:300], "metadata": d.metadata} for d in sources],
    }


# ============================================================================
# NODE 11: OUTPUT GUARDRAILS
# Post-generation safety check for fabricated claims.
# ============================================================================

async def guardrails_node(state: dict) -> dict:
    """Final safety check: detect fabricated claims in the generated answer.

    Scans for patterns like unsupported award claims, fabricated controversies,
    unverified revenue figures, and speculative statements. If any claim
    cannot be verified against the provided context, the answer is replaced
    with a safe refusal message.

    This is the last line of defense before the answer reaches the user.
    """
    if state.get("blocked"):
        return state
    answer = state.get("draft_answer", "")
    context = state.get("merged_context", "")
    trace_id = state.get("trace_id", "")

    with tracing_service.span(trace_id, "guardrails"):
        is_safe, reason, issues = await guardrail_service.check_output(answer, context)
        if not is_safe:
            logger.warning(f"Guardrail issues: {issues}")
            refusal = guardrail_service.get_safe_refusal(
                "The generated response contained claims that could not be verified against available sources."
            )
            return {
                **state,
                "final_answer": refusal,
                "blocked": True,
                "refusal_reason": refusal,
            }

    return {**state, "final_answer": answer}


# ============================================================================
# NODE 12: FINALIZE RESPONSE
# Ends the trace, computes latency, and formats the final output.
# ============================================================================

async def finalize_response_node(state: dict) -> dict:
    """Finalize the response: end the trace and compute total latency.

    If the query was blocked at any point, the refusal message is used
    as the final answer. Otherwise, the guardrail-verified answer is returned.
    """
    trace_id = state.get("trace_id", "")
    trace = tracing_service.end_trace(trace_id)
    latency = trace["total_duration_ms"] if trace else 0.0

    if state.get("blocked"):
        return {
            **state,
            "final_answer": state.get("refusal_reason", SAFE_REFUSAL_MESSAGE),
            "latency_ms": latency,
        }

    return {**state, "latency_ms": latency}
