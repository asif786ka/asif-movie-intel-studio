# Architecture — Asif Movie Intel Studio

## System Overview

Asif Movie Intel Studio is a production-style RAG (Retrieval-Augmented Generation) application that combines structured movie data from TMDB with unstructured document analysis. The system uses a LangGraph-orchestrated multi-step pipeline to intelligently route queries, retrieve context, and generate grounded answers with citations.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React + Vite Frontend                     │
│  Home │ Chat │ Search │ Compare │ Upload │ Dashboard │ Eval      │
│  (React Router, Zustand, TanStack Query, Tailwind CSS)           │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────────────┐
│             Express API Proxy (Node.js, dev mode)                │
│  /api/healthz (local) │ /api/* → proxy to Python backend         │
│  (In production Docker, Nginx proxies /api/* directly)           │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP proxy
┌────────────────────────▼────────────────────────────────────────┐
│                     FastAPI Backend (Python)                      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              LangGraph Workflow Engine                    │    │
│  │                                                          │    │
│  │  validate → classify → route ─┬─ TMDB lookup             │    │
│  │                                ├─ RAG retrieval            │    │
│  │                                └─ Hybrid (both)           │    │
│  │                                                          │    │
│  │  merge context → grade evidence → generate → guardrails   │    │
│  │  → extract citations → finalize response                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  TMDB Service │  │ LLM Provider │  │  Embedding Service │    │
│  │  (API + seed) │  │ (OpenAI/Mock)│  │  (text-embed-3-sm) │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  ChromaDB     │  │  Guardrails  │  │  Tracing Service   │    │
│  │  Vector Store │  │  Service     │  │  (spans, traces)   │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### Frontend (React + Vite)

- **Router**: React Router with 7 routes (/, /chat, /search, /compare, /upload, /admin, /eval)
- **State Management**: Zustand stores for chat, search, upload, and compare state
- **Data Fetching**: TanStack React Query for caching and mutations
- **API Layer**: Dedicated client modules (chatApi, movieApi, uploadApi, metricsApi)
- **Streaming**: SSE via POST to `/api/chat/stream` with event types (start, content, metadata, done)

### Backend (FastAPI + LangGraph)

- **API Layer**: FastAPI with versioned endpoints under `/api/`
- **Workflow Engine**: LangGraph StateGraph with 12 nodes and conditional routing
- **LLM Provider**: Abstraction layer supporting OpenAI, AWS Bedrock, and mock provider
- **Vector Store**: ChromaDB with persistent storage, seeded with sample documents on startup
- **TMDB Integration**: Live API with seed-data fallback for offline operation

### Data Flow

1. User query arrives via HTTP POST or SSE stream
2. Input validation checks for prompt injection and minimum length
3. Query classifier determines type: structured_only, rag_only, or hybrid
4. Router dispatches to appropriate retrieval path(s)
5. Context from TMDB and/or vector store is merged
6. Evidence grading evaluates sufficiency (with retry on insufficient evidence)
7. LLM generates answer using grounded context
8. Citation extractor links claims to sources
9. Guardrail checker validates answer against context
10. Finalized response streams back with metadata

### Storage Architecture

| Store | Technology | Purpose |
|-------|-----------|---------|
| Vector Store | ChromaDB | Document embeddings and similarity search |
| Metadata Store | In-memory dict | Query metrics, trace data, routing stats |
| Audit Store | In-memory list | Request/response audit log |
| Session Store | In-memory dict | Chat session history |

### Embedding Pipeline

Documents are chunked (500 tokens, 50-token overlap), embedded via OpenAI text-embedding-3-small (or SHA256 hash fallback), and stored in ChromaDB with metadata (movie_title, source_type, director, franchise, release_year).
