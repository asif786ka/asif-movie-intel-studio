# Asif Movie Intel Studio — Complete Step-by-Step Tutorial

> **Author**: Senior AI Technical Architect  
> **Audience**: Developers building production RAG systems  
> **Level**: Beginner to Advanced

---

## Table of Contents

1. [Architecture Snapshot](#1-architecture-snapshot)
2. [Getting Started: Setup & Installation](#2-getting-started)
3. [Backend Tutorial: FastAPI + LangGraph RAG Pipeline](#3-backend-tutorial)
4. [Frontend Tutorial: React + Vite Application](#4-frontend-tutorial)
5. [RAG Pipeline Explained: How It All Works](#5-rag-pipeline-explained)
6. [Adding Documents to RAG (Example: Tom Cruise)](#6-adding-documents-to-rag)
7. [Safety & Guardrails Deep Dive](#7-safety--guardrails)
8. [Modifying the Project: Common Tasks](#8-modifying-the-project)
9. [Deployment Guide](#9-deployment-guide)
10. [Scalability Analysis](#10-scalability-analysis)
11. [Evaluation Framework](#11-evaluation-framework)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Architecture Snapshot

### System Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                              │
│                                                                    │
│  React 19 + Vite + TypeScript + Tailwind CSS                      │
│  ┌──────┐ ┌──────┐ ┌────────┐ ┌───────┐ ┌──────┐ ┌─────┐ ┌────┐│
│  │ Home │ │ Chat │ │ Search │ │Compare│ │Upload│ │Admin│ │Eval││
│  └──────┘ └──────┘ └────────┘ └───────┘ └──────┘ └─────┘ └────┘│
│                                                                    │
│  State: Zustand    Data: TanStack Query    Streaming: SSE         │
└───────────────────────────┬────────────────────────────────────────┘
                            │ HTTP / SSE
┌───────────────────────────▼────────────────────────────────────────┐
│                      PROXY LAYER                                   │
│  Express API server — proxies /api/* to Python backend             │
│  Production: auto-spawns Python + health check before proxying     │
└───────────────────────────┬────────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────────┐
│                      BACKEND LAYER                                 │
│                                                                    │
│  FastAPI + LangGraph State Machine + LangChain                    │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              12-NODE RAG PIPELINE                            │  │
│  │                                                              │  │
│  │  ┌───────────┐    ┌──────────┐    ┌───────────┐            │  │
│  │  │ VALIDATE  │───▶│ CLASSIFY │───▶│   ROUTE   │            │  │
│  │  │  INPUT    │    │  QUERY   │    │   QUERY   │            │  │
│  │  └───────────┘    └──────────┘    └─────┬─────┘            │  │
│  │       │                          ┌──────┼──────┐            │  │
│  │   [blocked]                structured  rag  hybrid          │  │
│  │       │                      │      │      │                │  │
│  │       ▼                 ┌────▼──┐   │  ┌───▼────┐          │  │
│  │  ┌─────────┐            │ TMDB  │   │  │  TMDB  │          │  │
│  │  │FINALIZE │            │LOOKUP │   │  │ LOOKUP │          │  │
│  │  └─────────┘            └───┬───┘   │  └───┬────┘          │  │
│  │                             │       │      │                │  │
│  │                        [merge]      │  [retrieve]           │  │
│  │                             │       │      │                │  │
│  │                             │  ┌────▼──────▼────┐          │  │
│  │                             │  │ RETRIEVE DOCS  │          │  │
│  │                             │  └───────┬────────┘          │  │
│  │                             │          │                    │  │
│  │                             │  ┌───────▼────────┐          │  │
│  │                             │  │  RERANK DOCS   │          │  │
│  │                             │  └───────┬────────┘          │  │
│  │                             │          │                    │  │
│  │                       ┌─────▼──────────▼─────┐             │  │
│  │                       │    MERGE CONTEXT      │             │  │
│  │                       └──────────┬────────────┘             │  │
│  │                                  │                          │  │
│  │                       ┌──────────▼────────────┐             │  │
│  │                       │   GRADE EVIDENCE      │             │  │
│  │                       └──────────┬────────────┘             │  │
│  │                    insufficient  │  sufficient              │  │
│  │                    (retry once)  │     │                    │  │
│  │                                  │     │                    │  │
│  │                       ┌──────────▼────────────┐             │  │
│  │                       │  GENERATE ANSWER      │             │  │
│  │                       └──────────┬────────────┘             │  │
│  │                                  │                          │  │
│  │                       ┌──────────▼────────────┐             │  │
│  │                       │ EXTRACT CITATIONS     │             │  │
│  │                       └──────────┬────────────┘             │  │
│  │                                  │                          │  │
│  │                       ┌──────────▼────────────┐             │  │
│  │                       │    GUARDRAILS         │             │  │
│  │                       └──────────┬────────────┘             │  │
│  │                                  │                          │  │
│  │                       ┌──────────▼────────────┐             │  │
│  │                       │  FINALIZE RESPONSE    │──▶ END      │  │
│  │                       └───────────────────────┘             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────────┐  │
│  │ ChromaDB │  │ TMDB API │  │ OpenAI/   │  │  Tracing       │  │
│  │ Vectors  │  │ + Seed   │  │ Mock LLM  │  │  Service       │  │
│  └──────────┘  └──────────┘  └───────────┘  └────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend Framework | FastAPI | Async-native, auto OpenAPI docs, Pydantic validation |
| Workflow Engine | LangGraph | State machine with conditional edges, retry loops, observability |
| Vector Store | ChromaDB | Embedded, persistent, zero-config, great for < 1M docs |
| LLM Abstraction | Custom provider | Supports OpenAI, Bedrock, and MockLLM for demo mode |
| Frontend | React + Vite | Fast HMR, TypeScript, modern build pipeline |
| State Management | Zustand | Lightweight, no boilerplate, TypeScript-first |
| Server State | TanStack Query | Caching, deduplication, background refetching |
| Streaming | SSE (POST) | Works through proxies, no WebSocket infrastructure needed |

---

## 2. Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- pnpm 10+

### Step 1: Clone the Repository

```bash
git clone https://github.com/asif786ka/asif-movie-intel-studio.git
cd asif-movie-intel-studio
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Install Node.js dependencies
pnpm install
```

### Step 3: Configure Environment Variables (Optional)

The app works fully in demo mode without any API keys. For the full experience:

```bash
# Optional: TMDB API key for live movie data (free at themoviedb.org)
export TMDB_API_KEY="your_tmdb_api_key"

# Optional: OpenAI API key for real AI-powered chat
export OPENAI_API_KEY="your_openai_api_key"
```

**Without API keys**: The app uses seed data (20 built-in movies) and a mock LLM.
**With TMDB key**: Access to TMDB's full database of hundreds of thousands of movies.
**With OpenAI key**: Intelligent, context-aware AI chat responses powered by GPT.

### Step 4: Start the Application

```bash
# Option A: Use the Makefile (recommended)
make dev

# Option B: Start individually
# Terminal 1 — Backend
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
cd artifacts/movie-studio && pnpm run dev
```

### Step 5: Verify It Works

```bash
# Health check
curl http://localhost:8000/api/health

# Search for a movie
curl "http://localhost:8000/api/movies/search?query=inception"

# Ask the AI chat
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about Interstellar", "session_id": "test"}'
```

Open your browser to `http://localhost:5173` (or whichever port Vite reports) to see the frontend.

---

## 3. Backend Tutorial

### Step 1: Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app bootstrap (middleware, routes, startup)
│   ├── api/                 # Route handlers
│   │   ├── routes_chat.py   # POST /chat/query, POST /chat/stream
│   │   ├── routes_movies.py # GET /movies/search, GET /movies/{id}
│   │   ├── routes_upload.py # POST /upload/document
│   │   ├── routes_eval.py   # POST /eval/run, GET /eval/metrics
│   │   └── routes_health.py # GET /health, GET /ready
│   ├── core/                # Configuration and policies
│   │   ├── config.py        # Pydantic Settings (env vars → typed config)
│   │   ├── prompts.py       # All LLM prompts (centralized, versioned)
│   │   ├── versioning.py    # Prompt and pipeline version tracking
│   │   ├── security.py      # Prompt injection detection, rate limiting
│   │   ├── constants.py     # Route types, refusal messages, limits
│   │   └── logging.py       # Structured JSON logging
│   ├── graph/               # LangGraph workflow
│   │   ├── state.py         # GraphState Pydantic model (35 fields)
│   │   ├── nodes.py         # 12 async pipeline node functions
│   │   └── workflow.py      # StateGraph assembly + conditional edges
│   ├── services/            # Business logic services
│   │   ├── bedrock_service.py    # LLM provider abstraction
│   │   ├── tmdb_service.py       # TMDB API + seed data fallback
│   │   ├── embedding_service.py  # OpenAI embeddings + SHA256 fallback
│   │   ├── retrieval_service.py  # ChromaDB vector search
│   │   ├── rerank_service.py     # Document re-ranking
│   │   ├── citation_service.py   # [Source N] extraction and validation
│   │   ├── guardrail_service.py  # 3-layer safety enforcement
│   │   ├── ingestion_service.py  # Document chunking + embedding
│   │   └── tracing_service.py    # Request tracing with spans
│   ├── db/
│   │   ├── vector_store.py  # ChromaDB collection management
│   │   ├── metadata_store.py # In-memory metrics and routing stats
│   │   └── audit_store.py   # Request/response audit log
│   └── sample_data/
│       ├── docs/            # Sample documents for seeding
│       │   ├── interstellar_review.txt
│       │   ├── dune_timeline.txt
│       │   ├── oppenheimer_awards.txt
│       │   ├── villeneuve_analysis.txt
│       │   └── tom_cruise_career.txt
│       └── seed_movies.json # 20 seed movies for demo mode
├── tests/                   # Pytest suite (27 tests)
├── requirements.txt
└── Dockerfile
```

### Step 2: How the LangGraph Pipeline Works

The heart of the backend is the 12-node LangGraph state machine in `graph/workflow.py`.

**State Machine Design**:
- Every node receives the full state dict and returns a new merged state
- Conditional edges use simple Python functions that inspect state fields
- The `blocked` field acts as a global circuit breaker — once set, all nodes short-circuit

**Key Design Pattern — Immutable State**:
```python
# CORRECT: Return new state with merged updates
async def my_node(state: dict) -> dict:
    result = await do_work(state["query"])
    return {**state, "result": result}

# WRONG: Never mutate state in place
async def my_node(state: dict) -> dict:
    state["result"] = await do_work(state["query"])  # DON'T DO THIS
    return state
```

### Step 3: How Routing Works

The `classify_query_node` uses the LLM to classify queries:

1. **structured_only** → TMDB API only (cheapest path)
   - "What year was Inception released?"
   - "Who directed The Dark Knight?"

2. **rag_only** → ChromaDB vector search only
   - "Explain the philosophical themes in Interstellar"
   - "Tell me about Tom Cruise's career"

3. **hybrid** → Both TMDB + ChromaDB (most comprehensive)
   - "Compare Interstellar and Dune by box office and themes"

The classifier uses few-shot examples for reliability and falls back to keyword heuristics when the LLM returns unexpected output.

### Step 4: Adding a New API Endpoint

```python
# 1. Create route file: backend/app/api/routes_custom.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/custom/endpoint")
async def my_endpoint():
    return {"data": "result"}

# 2. Register in main.py:
from app.api.routes_custom import router as custom_router
app.include_router(custom_router, prefix="/api")
```

### Step 5: Adding a New LangGraph Node

```python
# 1. Define the node in graph/nodes.py
async def my_custom_node(state: dict) -> dict:
    if state.get("blocked"):
        return state  # Always check blocked first
    # Do your work here
    result = await some_service.process(state["query"])
    return {**state, "my_result": result}

# 2. Register in graph/workflow.py
workflow.add_node("my_custom", my_custom_node)
workflow.add_edge("previous_node", "my_custom")
workflow.add_edge("my_custom", "next_node")
```

---

## 4. Frontend Tutorial

### Step 1: Project Structure

```
artifacts/movie-studio/src/
├── App.tsx                  # Root component (providers + router)
├── main.tsx                 # Entry point (renders App into DOM)
├── components/
│   ├── AppLayout.tsx        # Sidebar nav + content area
│   └── ui/                  # shadcn/ui component library
├── hooks/
│   ├── use-movies.ts        # Movie search/details/compare hooks
│   ├── use-upload.ts        # File upload with XHR progress tracking
│   └── use-chat.ts          # SSE streaming chat hook
├── lib/
│   ├── api/                 # API client modules
│   │   ├── chatApi.ts       # POST /chat/query, POST /chat/stream
│   │   ├── movieApi.ts      # GET /movies/search, GET /movies/{id}
│   │   ├── uploadApi.ts     # POST /upload/document
│   │   └── metricsApi.ts    # GET /eval/metrics
│   ├── types.ts             # TypeScript interfaces (no `any` types)
│   └── utils.ts             # Shared utilities
├── pages/
│   ├── Home.tsx             # Landing page with architecture overview
│   ├── Chat.tsx             # Streaming chat with citations sidebar
│   ├── Search.tsx           # Movie search grid with detail modals
│   ├── Compare.tsx          # Multi-movie comparison (2-5 films)
│   ├── Upload.tsx           # Document upload with progress bars
│   ├── Admin.tsx            # System dashboard (6 stat cards)
│   └── Eval.tsx             # Evaluation runner and metric display
└── stores/
    └── appStore.ts          # Zustand stores (chat, search, upload, compare)
```

### Step 2: How the Provider Stack Works

```tsx
// App.tsx — Components are nested for proper context propagation
<QueryClientProvider>    {/* TanStack Query cache provider */}
  <TooltipProvider>      {/* UI tooltip context */}
    <BrowserRouter>      {/* React Router with artifact basename */}
      <AppLayout>        {/* Sidebar navigation + content */}
        <Routes>         {/* Page routing */}
          ...
        </Routes>
      </AppLayout>
    </BrowserRouter>
  </TooltipProvider>
</QueryClientProvider>
```

### Step 3: How SSE Streaming Chat Works

The Chat page uses Server-Sent Events for real-time token streaming:

```
1. User types message → onClick calls useChatStream.send(message)
2. Frontend sends POST /api/chat/stream with { query, session_id }
3. Express proxy forwards to Python FastAPI (no body parsing for SSE)
4. FastAPI generates tokens, sends SSE events:
   - event: start      → { session_id, trace_id }
   - event: content     → { token: "The" }
   - event: content     → { token: " movie" }
   - event: metadata    → { route_type, citations, sources }
   - event: done        → { latency_ms }
5. Frontend appends each token to the message display in real-time
6. On "done" event, citations sidebar populates with source links
```

### Step 4: How Debounced Search Works

```typescript
// use-movies.ts — Built-in debounce prevents API spam
export function useMovieSearch(initialQuery = "", debounceMs = 300) {
  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);

  useEffect(() => {
    // Wait 300ms after user stops typing before firing API call
    const timer = setTimeout(() => setDebouncedQuery(query), debounceMs);
    return () => clearTimeout(timer);
  }, [query, debounceMs]);

  // TanStack Query only fires when debouncedQuery changes
  const result = useQuery({
    queryKey: ["/api/movies/search", debouncedQuery],
    queryFn: () => movieApi.searchMovies(debouncedQuery),
    enabled: !!debouncedQuery,  // Don't fetch empty queries
  });

  return { query, setQuery, debouncedQuery, ...result };
}
```

### Step 5: Adding a New Page

```tsx
// 1. Create page: src/pages/MyPage.tsx
export default function MyPage() {
  return <div className="p-6"><h2>My Page</h2></div>;
}

// 2. Add route in App.tsx:
import MyPage from "./pages/MyPage";
<Route path="/my-page" element={<MyPage />} />

// 3. Add nav link in AppLayout.tsx:
{ to: "/my-page", icon: Star, label: "My Page" }
```

---

## 5. RAG Pipeline Explained

### What is RAG?

Retrieval-Augmented Generation (RAG) enhances LLM responses by:
1. **Retrieving** relevant documents from a knowledge base
2. **Augmenting** the LLM prompt with retrieved context
3. **Generating** a grounded answer that cites specific sources

This prevents hallucination by making the LLM answer from verified documents instead of relying on its training data alone.

### How Documents Become Searchable

```
Document Upload Flow:
                                                    
  .txt/.md file ──▶ Chunk Text ──▶ Generate Embeddings ──▶ Store in ChromaDB
                    (500 chars,     (OpenAI text-          (vectors + text
                     sentences)      embedding-3-small,     + metadata)
                                     1536 dimensions)
                                                    
Each chunk gets:
  - A unique ID (job_id + chunk_index)
  - The raw text content
  - A 1536-dimensional embedding vector
  - Metadata (movie_title, source_type, actor, director, etc.)
```

### How Queries Find Relevant Documents

```
Query: "Tell me about Tom Cruise's Mission Impossible stunts"

Step 1 — Embed the query:
  "Tell me about Tom Cruise's Mission Impossible stunts"
    → [0.023, -0.145, 0.891, ...] (1536 dimensions)

Step 2 — Search ChromaDB:
  Find top-10 chunks with highest cosine similarity to the query vector
    → Chunk from tom_cruise_career.txt: "Mission: Impossible franchise..." (0.89)
    → Chunk from tom_cruise_career.txt: "Practical Stunts and Physical..." (0.85)
    → Chunk from villeneuve_analysis.txt: "Denis Villeneuve..." (0.21) — low score

Step 3 — Rerank:
  Re-score chunks by keyword overlap with the original query
    → Keep top-5 most relevant chunks

Step 4 — Format as context:
  "[Source 1] (analysis - Tom Cruise Films): Tom Cruise, born..."
  "[Source 2] (analysis - Tom Cruise Films): The Mission: Impossible..."
```

### Our RAG Implementation: Three Routes

**Structured Only Route (Cheapest)**:
```
Query: "What year was Inception released?"

Step 1 — Classify: structured_only (factual data question)
Step 2 — TMDB Lookup: Fetch from TMDB API → {release_date: "2010-07-15", ...}
Step 3 — Generate: LLM answers using only TMDB data
Step 4 — Finalize: Return answer (no document citations needed)
```

**RAG Only Route (Document Knowledge)**:
```
Query: "Tell me about Tom Cruise's career"

Step 1 — Classify: rag_only (needs document analysis)
Step 2 — Retrieve: Search ChromaDB → 10 chunks from tom_cruise_career.txt
Step 3 — Rerank: Score by relevance → top 5 chunks selected
Step 4 — Merge Context: Format with [Source N] numbering
Step 5 — Grade Evidence: Score 0.82 (sufficient — covers the topic)
Step 6 — Generate: LLM creates answer using ONLY the context
Step 7 — Extract Citations: Parse [Source 1], [Source 2] references
Step 8 — Guardrails: Check for fabricated claims → PASS
Step 9 — Finalize: Return answer + citations + metadata
```

**Hybrid Route (Most Comprehensive)**:
```
Query: "Compare Top Gun and Interstellar by box office and themes"

Step 1 — Classify: hybrid (needs TMDB data + document analysis)
Step 2a — TMDB Lookup: Fetch structured data for both movies
Step 2b — Retrieve + Rerank: Search ChromaDB for thematic analysis
Step 3 — Merge Context: Combine TMDB data + [Source N] documents
Step 4-9 — Same as RAG path (grade, generate, cite, guardrail, finalize)
```

---

## 6. Adding Documents to RAG

This section shows how to add new knowledge to the RAG system, using Tom Cruise as a working example.

### Method 1: Using the Web UI (Easiest)

1. **Create a text file** — Write or download information about the topic
2. **Go to the Ingest Docs page** in the app (sidebar → "Ingest Docs")
3. **Upload the file** with metadata:
   - Movie Title: "Tom Cruise Films"
   - Source Type: "analysis"
   - Actor: "Tom Cruise"
4. **Wait for processing** — the system chunks, embeds, and stores the document
5. **Test in chat** — ask "Tell me about Tom Cruise" and see the AI respond with sourced information

### Method 2: Add as Seed Data (Auto-loaded on Startup)

For documents that should always be available:

**Step 1**: Create the document file:
```bash
# Create: backend/app/sample_data/docs/tom_cruise_career.txt
# Write comprehensive content about the topic
```

**Step 2**: Register it in the seed script (`backend/app/scripts/seed_data.py`):
```python
DOC_METADATA = {
    # ... existing entries ...
    "tom_cruise_career.txt": DocumentMetadata(
        movie_title="Tom Cruise Films",
        source_type="analysis",
        actor="Tom Cruise",
    ),
}
```

**Step 3**: Clear and re-seed the vector store:
```bash
cd backend
rm -rf data/chroma          # Delete old vectors
python -m app.scripts.ingest_sample_docs   # Re-seed with all docs
```

**Step 4**: Restart the backend and test:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Test the query
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about Tom Cruise career", "session_id": "test"}'
```

### Method 3: Programmatic Upload via API

```bash
# Upload a document via the API
curl -X POST http://localhost:8000/api/upload/document \
  -F "file=@my_document.txt" \
  -F "movie_title=Tom Cruise Films" \
  -F "source_type=analysis" \
  -F "actor=Tom Cruise"
```

```python
# Or via Python
import httpx

with open("tom_cruise_career.txt", "rb") as f:
    resp = httpx.post(
        "http://localhost:8000/api/upload/document",
        files={"file": ("tom_cruise_career.txt", f, "text/plain")},
        data={
            "movie_title": "Tom Cruise Films",
            "source_type": "analysis",
            "actor": "Tom Cruise",
        },
    )
print(resp.json())
```

### What Makes a Good RAG Document?

| Quality | Good | Bad |
|---------|------|-----|
| Length | 500-5000 words | < 50 words or > 50000 words |
| Structure | Paragraphs with clear topics | Random bullet points |
| Facts | Specific names, dates, numbers | Vague generalizations |
| Sources | Verified information | Unverified rumors |
| Metadata | Accurate movie_title, actor, director | Missing or wrong metadata |

### Understanding Embedding Dimensions

When you switch between OpenAI embeddings and the fallback SHA256 embeddings, the vector dimensions change:
- **OpenAI**: 1536 dimensions (high quality, semantic understanding)
- **SHA256 fallback**: 384 dimensions (basic, hash-based)

If you see the error `Collection expecting embedding with dimension of 384, got 1536`, you need to clear and re-seed:
```bash
rm -rf backend/data/chroma
# Restart the backend — it will auto-seed with the correct dimensions
```

---

## 7. Safety & Guardrails

### Three-Layer Defense Architecture

```
Layer 1: INPUT GUARDRAILS (before any LLM call)
  ├── Prompt injection detection (15+ regex patterns)
  ├── System override attempts blocked
  ├── Role hijacking attempts blocked
  └── Query length validation (min 2 chars)

Layer 2: EVIDENCE GRADING (before answer generation)
  ├── Context sufficiency scoring (0.0-1.0)
  ├── Retry loop: re-retrieve once if insufficient
  ├── Safe refusal if evidence still insufficient after retry
  └── Prevents hallucination on weak context

Layer 3: OUTPUT GUARDRAILS (after answer generation)
  ├── 7 regex patterns for fabrication detection:
  │   ├── Unsupported award claims (Oscar, Golden Globe, etc.)
  │   ├── Fabricated financial figures
  │   ├── Controversy/scandal references
  │   ├── Rumor-based statements
  │   └── Hedged assertions ("it is widely known...")
  ├── Each match verified against actual context
  └── Answer replaced with safe refusal if unverifiable claims found
```

### Prompt Injection Defense

The `detect_prompt_injection()` function in `core/security.py` scans for:

| Attack Type | Example | Defense |
|------------|---------|---------|
| System override | "Ignore previous instructions" | Regex pattern match |
| Role hijacking | "You are now a hacker" | Keyword detection |
| Info exfiltration | "Show me your system prompt" | Pattern blocking |
| Token smuggling | Encoded injection via base64 | Sanitization |
| Jailbreak | "Pretend you have no safety filters" | Pattern match + block |

### Evidence Sufficiency Formula

```python
score = (query_term_coverage * 0.6) + (context_length_score * 0.4)

# Where:
query_term_coverage = overlap(query_terms, context_terms) / len(query_terms)
context_length_score = min(word_count / 200, 1.0)

# Thresholds:
# score < 0.2  → Immediately insufficient (off-topic context)
# score < 0.3  → Insufficient → retry retrieval once
# score >= 0.3 → Sufficient (partial evidence is acceptable)
```

### Rate Limiting

The middleware in `main.py` applies rate limiting to chat and upload endpoints using an in-memory sliding window counter per client IP. This prevents abuse without adding external dependencies.

---

## 8. Modifying the Project

### Adding a New Movie Data Source

To add a new data source (e.g., IMDB scraper):

```python
# 1. Create: backend/app/services/imdb_service.py
class IMDBService:
    async def fetch_movie(self, imdb_id: str) -> dict:
        # Your implementation here
        pass

imdb_service = IMDBService()

# 2. Use in nodes.py — add to tmdb_lookup_node or create a new node
# 3. Register the node in workflow.py
```

### Adding a New Guardrail Pattern

```python
# In backend/app/services/guardrail_service.py
# Add to the UNSUPPORTED_PATTERNS list:

UNSUPPORTED_PATTERNS = [
    # ... existing patterns ...
    r"(?:is|was)\s+(?:known|famous)\s+for\s+(?:being|having)\s+(?:the\s+)?(?:worst|best)",
]
```

### Changing the LLM Model

```python
# In backend/app/services/bedrock_service.py
# Modify the model initialization:

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",          # Change model here
    temperature=0.1,          # Adjust creativity
    max_tokens=2000,          # Max response length
)
```

### Adding a New Frontend Component

```tsx
// 1. Create component: src/components/MovieCard.tsx
interface MovieCardProps {
  title: string;
  year: number;
  poster: string;
}

export function MovieCard({ title, year, poster }: MovieCardProps) {
  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <img src={poster} alt={title} className="rounded" />
      <h3 className="text-gold-400 mt-2">{title}</h3>
      <p className="text-gray-400">{year}</p>
    </div>
  );
}

// 2. Use in any page:
import { MovieCard } from "../components/MovieCard";
```

### Updating the API Client

When you add a new backend endpoint, update the frontend API client:

```typescript
// In src/lib/api/movieApi.ts
const API_BASE = import.meta.env.BASE_URL + "api";

export const movieApi = {
  // ... existing methods ...
  
  getMovieTrivia: async (movieId: number) => {
    const resp = await fetch(`${API_BASE}/movies/${movieId}/trivia`);
    return resp.json();
  },
};
```

---

## 9. Deployment Guide

### Deploying to Production

The Express API server includes production-ready features:
- Automatically spawns the Python backend as a child process
- Installs Python dependencies on first boot
- Waits for the Python backend to pass health checks (polls every 3s, up to 3 minutes)
- Returns 503 "starting up" responses while the backend initializes
- Auto-restarts the Python process if it crashes

### Deploying with Docker

```bash
# Build and start all services
docker-compose up --build -d

# This starts:
#   - Python backend on port 8000
#   - Frontend on port 3000

# With optional Redis cache
docker-compose --profile with-cache up --build -d

# Stop everything
docker-compose down
```

### Deploying on AWS / Cloud

For production cloud deployment:

```bash
# 1. Build the frontend
cd artifacts/movie-studio && pnpm run build

# 2. Build Docker images
docker build -t movie-intel-backend ./backend
docker build -t movie-intel-frontend ./artifacts/movie-studio

# 3. Push to ECR/Docker Hub
docker push your-registry/movie-intel-backend
docker push your-registry/movie-intel-frontend

# 4. Deploy to ECS/EKS/Cloud Run with env vars:
#    TMDB_API_KEY, OPENAI_API_KEY, CHROMA_PERSIST_DIR
```

### Environment Variables for Production

| Variable | Required | Description |
|----------|----------|-------------|
| `TMDB_API_KEY` | Recommended | TMDB API key for live movie data |
| `OPENAI_API_KEY` | Recommended | OpenAI API key for AI chat |
| `LLM_PROVIDER` | No | "openai" (default), "bedrock", or auto-fallback |
| `CHROMA_PERSIST_DIR` | No | ChromaDB storage path (default: ./data/chroma) |
| `LANGSMITH_TRACING_ENABLED` | No | Enable LangSmith observability |
| `OTEL_ENABLED` | No | Enable OpenTelemetry tracing |

### Updating After Deployment

```bash
# 1. Make your code changes

# 2. Test locally
make test

# 3. Push to GitHub
git add . && git commit -m "Your changes" && git push

# 4a. Deploy to your hosting platform
# 4b. On Docker: Rebuild and restart containers
docker-compose up --build -d

# 5. Verify deployment
curl https://your-domain.com/api/health
```

---

## 10. Scalability Analysis

### Current Architecture (Demo Scale)

| Component | Current | Production Alternative |
|-----------|---------|----------------------|
| Vector Store | ChromaDB (embedded) | Pinecone, Weaviate, Qdrant (managed) |
| LLM | OpenAI API / Mock | Azure OpenAI, AWS Bedrock, self-hosted |
| Session Store | In-memory dict | Redis, DynamoDB |
| Audit Store | In-memory list | PostgreSQL, CloudWatch Logs |
| Rate Limiter | In-memory counter | Redis-based (distributed) |
| Metadata Store | In-memory dict | PostgreSQL, TimescaleDB |
| Embeddings | Per-request API call | Cached embeddings, batch processing |

### Scaling Strategy

**Horizontal Scaling**:
1. Stateless backend — move session/audit stores to Redis/PostgreSQL
2. ChromaDB → managed vector DB (Pinecone/Qdrant) for distributed search
3. Load balancer in front of multiple FastAPI instances
4. Background job queue (Celery/Redis) for document ingestion

**Vertical Scaling**:
1. Embedding cache — avoid re-embedding the same text
2. LLM response cache — cache answers for identical queries
3. Connection pooling for TMDB API calls
4. Async batch processing for bulk uploads

**Cost Optimization**:
1. Route classifier reduces unnecessary RAG lookups (structured_only path is cheapest)
2. Evidence grading prevents wasted LLM tokens on insufficient context
3. Embedding fallback (SHA256 hash) works without OpenAI API key
4. Seed data fallback works without TMDB API key

---

## 11. Evaluation Framework

### Why Evaluation Matters

RAG systems can fail in subtle ways:
- **Routing errors**: Sending a theme question to TMDB instead of documents
- **Hallucination**: Making up facts not in the retrieved context
- **Citation errors**: Referencing non-existent sources
- **Safety failures**: Not blocking prompt injection attempts
- **Context gaps**: Answering with insufficient evidence

### Our Evaluation Datasets

| Dataset | Queries | Purpose |
|---------|---------|---------|
| `movie_eval_set.json` | 20 | End-to-end answer quality across all routes |
| `routing_eval_set.json` | 20 | Query classification accuracy |
| `adversarial_queries.json` | 15 | Security and guardrail robustness |

### Custom Metrics

| Metric | What It Measures | How | Threshold |
|--------|-----------------|-----|-----------|
| Citation Accuracy | Are [Source N] refs valid? | Check source index bounds | >= 80% |
| Unsupported Claim Rate | Claims without context support? | Word overlap < 20% | <= 10% |
| Timeline Consistency | Temporal logic errors? | Before/after + year order | >= 80% |
| Source Diversity | Using varied sources? | Unique types + titles / total | >= 50% |
| Routing Correctness | Right classification? | Predicted vs expected route | >= 85% |
| Adversarial Block Rate | Blocking injections? | Blocked / expected-blocked | >= 90% |
| Faithfulness | Citations when expected? | Has-citations / expected-citations | >= 70% |
| Answer Relevancy | Keywords in answer? | Found keywords / expected keywords | >= 70% |

### Running Evaluations

```bash
# Run the full evaluation suite
python eval/ragas_runner.py --all

# Run a specific dataset
python eval/ragas_runner.py --dataset movie_eval_set --max-queries 20

# Run directly via LangGraph (no HTTP)
python eval/ragas_runner.py --dataset routing_eval_set --direct

# Results are saved to eval/results/ as timestamped JSON files
```

### Interpreting Results

```
============================================================
EVALUATION REPORT: movie_eval_set
============================================================
  [PASS] citation_accuracy: 85.0% (threshold: 80%)
         Percentage of citations correctly referencing source material
  [PASS] unsupported_claim_rate: 5.0% (threshold: 10%)
         Rate of claims not supported by provided context
  [PASS] timeline_consistency: 92.0% (threshold: 80%)
         Consistency of temporal references in answers
  [FAIL] source_diversity: 45.0% (threshold: 50%)
         Diversity of sources used across answers
  [PASS] routing_correctness: 90.0% (threshold: 85%)
         Accuracy of query routing decisions

  Overall: 4/5 metrics passed
============================================================
```

### Improving Failing Metrics

| Failing Metric | Root Cause | Fix |
|---------------|-----------|-----|
| Source Diversity low | Not enough varied documents | Ingest more diverse content (interviews, behind-the-scenes, etc.) |
| Routing errors | LLM misclassifying edge cases | Add more few-shot examples to QUERY_CLASSIFIER_PROMPT |
| Citation accuracy low | LLM not citing properly | Strengthen citation rules in SYSTEM_PROMPT |
| Unsupported claims high | Weak guardrail patterns | Add more regex patterns to UNSUPPORTED_PATTERNS |
| Adversarial failures | New injection patterns | Update detect_prompt_injection() with new patterns |

---

## 12. Troubleshooting

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "Collection expecting embedding with dimension of 384, got 1536" | Switched between OpenAI and mock embeddings | Delete `backend/data/chroma/` and restart |
| "I don't have sufficient evidence" for all questions | No documents in vector store OR asking about topics not covered | Upload relevant documents via Ingest Docs page |
| 504 Gateway Timeout in production | Python backend still starting | Wait 10-30 seconds, the health check will route requests once ready |
| Chat shows no response | OpenAI API key invalid or expired | Check the OPENAI_API_KEY environment variable |
| Movie search returns no results | TMDB API key missing | Add TMDB_API_KEY or use the 20 built-in seed movies |
| Port already in use | Previous process still running | Kill: `pkill -f uvicorn` or `pkill -f "node.*api-server"` |

### How to Debug the Pipeline

```bash
# 1. Check backend health
curl http://localhost:8000/api/health

# 2. Check readiness with versions
curl http://localhost:8000/api/ready

# 3. Test a non-streaming query (shows full response with metadata)
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Inception about?", "session_id": "debug"}'

# 4. Check the route type, trace ID, and latency in the response

# 5. View backend logs for pipeline trace
# Look for structured JSON logs showing each node's execution
```

---

## Summary

Asif Movie Intel Studio demonstrates production RAG architecture patterns:

1. **LangGraph state machine** — Declarative workflow with conditional routing, retry loops, and circuit breakers
2. **Three-layer safety** — Input guardrails, evidence grading, output verification
3. **Hybrid retrieval** — Intelligent routing between structured (TMDB) and unstructured (vector) data
4. **Observable pipeline** — Trace IDs, spans, latency tracking, and version tracking
5. **Comprehensive evaluation** — Custom metrics, adversarial testing, and automated scoring
6. **Extensible RAG** — Add any document (actors, directors, reviews) and the AI learns from it instantly

The architecture is designed to scale from demo mode (all in-memory, mock LLM) to production (managed vector DB, OpenAI, Redis, PostgreSQL) without architectural changes.
