from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Asif Movie Intel Studio"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: str = "*"
    backend_port: int = 8000

    tmdb_api_key: Optional[str] = None
    tmdb_base_url: str = "https://api.themoviedb.org/3"

    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o"

    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    chroma_persist_dir: str = "./data/chroma"
    upload_dir: str = "./data/uploads"

    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "asif-movie-intel-studio"
    langsmith_tracing_enabled: bool = False

    otel_enabled: bool = False
    otel_service_name: str = "asif-movie-intel-studio"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    max_upload_size_mb: int = 50
    max_chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_retrieval: int = 10
    rerank_top_k: int = 5
    evidence_threshold: float = 0.3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
