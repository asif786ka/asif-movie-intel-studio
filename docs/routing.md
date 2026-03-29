# LangGraph Routing Logic — Asif Movie Intel Studio

## Overview

The routing system determines the optimal retrieval path for each user query. It uses a two-stage approach: LLM-based classification followed by deterministic routing through the LangGraph state machine.

## Query Classification

The `classify_query_node` uses the QUERY_CLASSIFIER_PROMPT to classify queries into three categories:

| Route | Description | Data Sources |
|-------|-------------|-------------|
| `structured_only` | Answerable with TMDB metadata (titles, dates, ratings, cast, crew, genres, box office) | TMDB API |
| `rag_only` | Requires unstructured analysis (reviews, themes, timelines, interviews) | ChromaDB vector store |
| `hybrid` | Needs both structured metadata AND unstructured analysis | TMDB API + ChromaDB |

### Classification Examples

```
"List top Nolan sci-fi movies"           → structured_only
"What is the rating of Inception?"       → structured_only
"Explain philosophical themes in X"      → rag_only
"Summarize critic reviews of Y"          → rag_only
"Compare X and Y by themes and box office" → hybrid
```

### Fallback Heuristics

If the LLM returns an unrecognized classification, keyword-based fallbacks activate:

- **Hybrid keywords**: "compare", "versus", "vs", "contrast", "both"
- **RAG keywords**: "theme", "review", "analysis", "explain", "summarize", "recurring", "philosophy"
- **Default**: structured_only

## LangGraph State Machine

```
                    ┌──────────────┐
                    │ validate_input│
                    └──────┬───────┘
                           │
                    blocked? ─── yes ──→ finalize_response ──→ END
                           │ no
                    ┌──────▼───────┐
                    │ classify_query│
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  route_query  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
      structured_only   rag_only     hybrid
              │            │            │
       ┌──────▼──────┐    │     ┌──────▼──────┐
       │ tmdb_lookup  │    │     │ tmdb_lookup  │
       └──────┬──────┘    │     └──────┬──────┘
              │            │            │
              │      ┌─────▼─────┐     │
              │      │retrieve_docs│◄───┘
              │      └─────┬─────┘
              │            │
              │      ┌─────▼─────┐
              │      │rerank_docs │
              │      └─────┬─────┘
              │            │
       ┌──────▼────────────▼──────┐
       │      merge_context        │
       └──────────┬───────────────┘
                  │
       ┌──────────▼───────────────┐
       │      grade_evidence       │
       └──────────┬───────────────┘
                  │
        insufficient & retries < 1 ──→ retrieve_docs (retry)
        insufficient & retries ≥ 1 ──→ finalize (refuse)
                  │ sufficient
       ┌──────────▼───────────────┐
       │     generate_answer       │
       └──────────┬───────────────┘
                  │
       ┌──────────▼───────────────┐
       │    extract_citations      │
       └──────────┬───────────────┘
                  │
       ┌──────────▼───────────────┐
       │       guardrails          │
       └──────────┬───────────────┘
                  │
       ┌──────────▼───────────────┐
       │   finalize_response       │──→ END
       └──────────────────────────┘
```

## Node Descriptions

| Node | Purpose |
|------|---------|
| `validate_input` | Check query length, run prompt injection detection |
| `classify_query` | LLM-based classification into structured/rag/hybrid |
| `route_query` | Pass-through node for conditional edge branching |
| `tmdb_lookup` | Search TMDB API for movie data (or use seed data) |
| `retrieve_docs` | Vector similarity search in ChromaDB |
| `rerank_docs` | Re-score retrieved documents for relevance |
| `merge_context` | Combine TMDB data and/or retrieved docs into context string |
| `grade_evidence` | Evaluate whether context sufficiently supports the query |
| `generate_answer` | LLM generates answer using context + system prompt |
| `extract_citations` | Parse and validate [Source N] references |
| `guardrails` | Check answer for fabrication and unsupported claims |
| `finalize_response` | End trace, compute latency, format final response |

## Evidence Retry Logic

If `grade_evidence` scores the context below the sufficiency threshold and the retry count is less than 1, the system loops back to `retrieve_docs` for a second retrieval attempt. This helps when the initial retrieval misses relevant documents.

After 1 retry, if evidence remains insufficient, the system returns a safe refusal message rather than generating a potentially unfaithful answer.

## Routing Metrics

The admin dashboard tracks routing distribution across all three paths, showing the percentage of queries routed to structured_only, rag_only, and hybrid. This helps identify if the classifier is skewing toward one path.
