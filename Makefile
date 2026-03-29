.PHONY: help dev backend frontend install test lint eval eval-all build docker clean

help:
        @echo "Asif Movie Intel Studio - Development Commands"
        @echo ""
        @echo "  make dev            Start backend and frontend in development mode"
        @echo "  make backend        Start Python FastAPI backend only"
        @echo "  make frontend       Start React+Vite frontend only"
        @echo "  make install        Install all dependencies"
        @echo "  make test           Run backend tests"
        @echo "  make test-frontend  Run frontend typecheck"
        @echo "  make lint           Run linters"
        @echo "  make eval           Run movie eval set"
        @echo "  make eval-all       Run all evaluation datasets"
        @echo "  make eval-routing   Run routing eval set"
        @echo "  make eval-adversarial Run adversarial query eval"
        @echo "  make build          Build frontend for production"
        @echo "  make docker         Build and start Docker containers"
        @echo "  make docker-down    Stop Docker containers"
        @echo "  make seed           Seed vector store with sample documents"
        @echo "  make clean          Clean build artifacts"

dev:
        @echo "Starting backend and frontend..."
        @make -j2 backend frontend

backend:
        cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
        pnpm --filter @workspace/movie-studio run dev

install:
        pip install -r backend/requirements.txt
        pnpm install

test:
        cd backend && python -m pytest tests/ -v

test-frontend:
        pnpm --filter @workspace/movie-studio exec tsc --noEmit

lint:
        cd backend && python -m ruff check .
        pnpm --filter @workspace/movie-studio exec tsc --noEmit

eval:
        python eval/ragas_runner.py --dataset movie_eval_set --max-queries 20

eval-all:
        python eval/ragas_runner.py --all

eval-routing:
        python eval/ragas_runner.py --dataset routing_eval_set

eval-adversarial:
        python eval/ragas_runner.py --dataset adversarial_queries

build:
        pnpm --filter @workspace/movie-studio run build

docker:
        docker compose up --build -d

docker-down:
        docker compose down

seed:
        cd backend && python -m app.scripts.ingest_sample_docs

clean:
        rm -rf artifacts/movie-studio/dist
        rm -rf backend/__pycache__ backend/app/**/__pycache__
        rm -rf eval/results/*.json
