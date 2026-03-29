# Asif Movie Intel Studio

A production-grade AI-powered movie research platform combining TMDB structured data with RAG (Retrieval-Augmented Generation) over unstructured film documents, orchestrated by a 12-node LangGraph workflow engine.

## Architecture Overview

### High-Level System Architecture

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
│                      PROXY LAYER (Express)                         │
│                                                                    │
│  • Proxies /api/* → Python FastAPI backend                        │
│  • In production: auto-spawns Python, health check, auto-restart  │
│  • SSE pass-through (no body parsing for streaming endpoints)      │
└───────────────────────────┬────────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────────┐
│                      BACKEND LAYER (FastAPI)                       │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              12-NODE LangGraph RAG PIPELINE                  │  │
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
│  │ ChromaDB │  │ TMDB API │  │ OpenAI /  │  │  Tracing &     │  │
│  │ Vectors  │  │ + Seed   │  │ Mock LLM  │  │  Observability │  │
│  └──────────┘  └──────────┘  └───────────┘  └────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### RAG Data Flow

```
Document Ingestion:
  .txt/.md file → Chunk (500 chars) → Embed (1536-dim) → Store in ChromaDB

Query Processing:
  User Query → Classify Route → [TMDB / Vector Search / Both]
    → Rerank → Merge Context → Grade Evidence → Generate Answer
    → Extract Citations → Guardrails Check → Stream Response
```

### Three-Layer Safety Architecture

```
Layer 1: INPUT GUARDRAILS        → Prompt injection detection (15+ patterns)
Layer 2: EVIDENCE GRADING        → Context sufficiency scoring + retry loop
Layer 3: OUTPUT GUARDRAILS       → Fabrication detection + claim verification
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TypeScript, Tailwind CSS, Zustand, TanStack Query |
| Backend | Python 3.12, FastAPI, LangGraph, LangChain |
| Vector Store | ChromaDB (persistent, embedded) |
| LLM | OpenAI GPT with mock fallback for demo mode |
| Embeddings | OpenAI text-embedding-3-small (SHA256 fallback) |
| Data Source | TMDB API with 20-movie seed data fallback |
| Evaluation | Custom RAGAS-inspired metrics framework |
| Infrastructure | Docker, Docker Compose, GitHub Actions CI |
| Proxy | Express 5 with http-proxy-middleware |

## Features

- **12-Node LangGraph Pipeline**: Full state machine with conditional routing, retry loops, and circuit breakers
- **Intelligent Query Routing**: LLM classifies queries into structured (TMDB), RAG (documents), or hybrid paths
- **Streaming Chat**: SSE-based streaming responses with real-time token delivery
- **Citation System**: Source-grounded answers with [Source N] citations linked to documents
- **Movie Comparison**: Multi-movie comparison engine across themes, reception, awards
- **Document Ingestion**: Upload .txt/.md files to expand the AI's knowledge base
- **Admin Dashboard**: Real-time metrics, routing distribution, prompt versions, trace summaries
- **Evaluation Suite**: Automated evaluation with 8 custom metrics and adversarial testing
- **Three-Layer Security**: Prompt injection detection, evidence grading, output guardrails
- **Extensible RAG**: Add documents about any actor, director, or movie — the AI learns instantly

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Home | `/` | Overview with architecture diagram and sample queries |
| Studio Chat | `/chat` | Streaming RAG chat with citations sidebar |
| Movie Database | `/search` | TMDB search with poster grid and detail modals |
| Compare | `/compare` | Multi-movie comparison (2-5 films) |
| Ingest Docs | `/upload` | Document upload to expand the RAG knowledge base |
| Dashboard | `/admin` | System metrics, routing stats, prompt versions |
| Evaluations | `/eval` | Run evaluations and view metric results |

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/asif786ka/asif-movie-intel-studio.git
cd asif-movie-intel-studio

# Install dependencies
pip install -r backend/requirements.txt
pnpm install
```

### 2. Configure (Optional)

The app works fully in demo mode without any API keys.

```bash
# Optional: For live TMDB movie data (free at themoviedb.org)
export TMDB_API_KEY="your_key"

# Optional: For real AI chat responses (platform.openai.com)
export OPENAI_API_KEY="your_key"
```

### 3. Run

```bash
# Start both backend and frontend
make dev

# Or individually:
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd artifacts/movie-studio && pnpm run dev
```

### 4. Add Knowledge to RAG

The AI can only answer questions about topics it has documents for. To add new knowledge:

**Via the Web UI**: Go to "Ingest Docs" page → upload a .txt file with movie/actor info

**Via the API**:
```bash
curl -X POST http://localhost:8000/api/upload/document \
  -F "file=@tom_cruise_career.txt" \
  -F "movie_title=Tom Cruise Films" \
  -F "source_type=analysis" \
  -F "actor=Tom Cruise"
```

**As seed data**: Add .txt files to `backend/app/sample_data/docs/` and register in `seed_data.py`

See the [Tutorial](docs/TUTORIAL.md#6-adding-documents-to-rag) for detailed instructions.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TMDB_API_KEY` | No | TMDB API key for live movie data (falls back to 20 seed movies) |
| `OPENAI_API_KEY` | No | OpenAI API key for AI chat (falls back to mock LLM) |
| `LLM_PROVIDER` | No | "openai" (default), "bedrock", or auto-fallback to mock |
| `CHROMA_PERSIST_DIR` | No | ChromaDB storage path (default: ./data/chroma) |
| `LANGSMITH_TRACING_ENABLED` | No | Enable LangSmith observability |
| `LANGSMITH_API_KEY` | No | LangSmith API key |
| `OTEL_ENABLED` | No | Enable OpenTelemetry instrumentation |

## API Endpoints

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/query` | Full RAG query with citations |
| POST | `/api/chat/stream` | SSE streaming response |
| GET | `/api/chat/history/{session_id}` | Chat session history |

### Movies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/movies/search?query=` | Search movies (TMDB or seed data) |
| GET | `/api/movies/{id}` | Movie details |
| GET | `/api/movies/{id}/credits` | Cast and crew |
| GET | `/api/movies/{id}/similar` | Similar movies |
| POST | `/api/movies/compare` | Compare multiple movies |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/document` | Upload document for RAG ingestion |
| POST | `/api/upload/bulk` | Bulk document upload |
| GET | `/api/upload/status/{job_id}` | Upload job status |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/eval/metrics` | System metrics and stats |
| POST | `/api/eval/run` | Run evaluation suite |
| GET | `/api/health` | Health check |
| GET | `/api/ready` | Readiness with version info |

## Docker Deployment

```bash
# Build and start all services
docker-compose up --build -d

# With optional Redis cache
docker-compose --profile with-cache up --build -d

# Stop services
docker-compose down
```

## Evaluation

The evaluation framework tests answer quality, routing accuracy, and adversarial robustness.

### Datasets

- **movie_eval_set.json**: 20 queries across structured, RAG, and hybrid routes
- **routing_eval_set.json**: 20 queries for route classification validation
- **adversarial_queries.json**: 15 prompt injection and jailbreak attempts

### Custom Metrics

| Metric | Description | Threshold |
|--------|-------------|-----------|
| Citation Accuracy | Valid [Source N] references | >= 80% |
| Unsupported Claim Rate | Claims without context support | <= 10% |
| Timeline Consistency | Temporal reference accuracy | >= 80% |
| Source Diversity | Variety of cited sources | >= 50% |
| Routing Correctness | Query classification accuracy | >= 85% |
| Adversarial Block Rate | Blocked injection attempts | >= 90% |

### Running Evaluations

```bash
# Run all evaluations
python eval/ragas_runner.py --all

# Run specific dataset
python eval/ragas_runner.py --dataset movie_eval_set --max-queries 20

# Run routing evaluation
python eval/ragas_runner.py --dataset routing_eval_set

# Results saved to eval/results/ as timestamped JSON
```

## Testing

```bash
# Backend tests (pytest — 27 tests)
make test
# or: cd backend && python -m pytest tests/ -v

# Frontend type checking
make test-frontend
# or: pnpm run typecheck

# Linting
make lint
```

## Project Structure

```
├── artifacts/movie-studio/   # React + Vite frontend
│   ├── src/
│   │   ├── components/       # UI components (AppLayout, shadcn/ui)
│   │   ├── hooks/            # React hooks (useChat, useMovieSearch, useUpload)
│   │   ├── lib/api/          # API client modules
│   │   ├── pages/            # 7 route page components
│   │   └── stores/           # Zustand state stores
│   └── Dockerfile
├── artifacts/api-server/     # Express proxy server
│   └── src/                  # Proxy config, health check, Python process mgmt
├── backend/                  # Python FastAPI backend
│   ├── app/
│   │   ├── api/              # Route handlers (chat, movies, upload, eval, health)
│   │   ├── core/             # Config, prompts, versioning, security, logging
│   │   ├── graph/            # LangGraph state (35 fields), 12 nodes, workflow
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # TMDB, LLM, embedding, retrieval, guardrails, etc.
│   │   ├── db/               # ChromaDB vector store, metadata, audit stores
│   │   └── sample_data/      # Seed documents + movies JSON
│   ├── tests/                # Pytest test suite (27 tests)
│   └── Dockerfile
├── eval/                     # Evaluation framework
│   ├── datasets/             # 3 eval datasets (55 total queries)
│   ├── ragas_runner.py       # Evaluation runner (HTTP + direct modes)
│   └── custom_metrics.py     # 8 custom metric implementations
├── docs/                     # Documentation
│   ├── TUTORIAL.md           # Complete step-by-step tutorial
│   ├── architecture.md       # System design and data flow
│   ├── security.md           # Guardrails and prompt injection defense
│   ├── evaluation.md         # Metrics and evaluation methodology
│   ├── prompt-versioning.md  # Version tracking strategy
│   └── routing.md            # LangGraph routing logic
├── docker-compose.yml        # Multi-service Docker orchestration
├── Makefile                  # Dev commands (dev, test, eval, docker, lint)
└── .github/workflows/ci.yml  # GitHub Actions CI
```

## Documentation

- **[Tutorial](docs/TUTORIAL.md)** — Complete step-by-step guide: setup, RAG explained, adding documents, deployment, modification, evaluation
- [Architecture](docs/architecture.md) — System design, component diagram, data flow
- [Security](docs/security.md) — Guardrails, prompt injection defense, tenant isolation
- [Evaluation](docs/evaluation.md) — Metrics definitions, eval methodology
- [Prompt Versioning](docs/prompt-versioning.md) — Version tracking strategy
- [Routing](docs/routing.md) — LangGraph routing logic and state machine

## License

MIT
