import hashlib
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self):
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from langchain_openai import OpenAIEmbeddings
                kwargs = {"model": "text-embedding-3-small"}
                if settings.openai_api_key:
                    kwargs["api_key"] = settings.openai_api_key
                if settings.openai_base_url:
                    kwargs["base_url"] = settings.openai_base_url
                self._model = OpenAIEmbeddings(**kwargs)
                logger.info("Using OpenAI embeddings")
            except Exception as e:
                logger.warning(f"OpenAI embeddings unavailable, using hash-based fallback: {e}")
                self._model = None
        return self._model

    def embed_text(self, text: str) -> list[float]:
        model = self._get_model()
        if model:
            try:
                return model.embed_query(text)
            except Exception as e:
                logger.warning(f"Embedding failed, using fallback: {e}")
        return self._hash_embed(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        if model:
            try:
                return model.embed_documents(texts)
            except Exception as e:
                logger.warning(f"Batch embedding failed, using fallback: {e}")
        return [self._hash_embed(t) for t in texts]

    @staticmethod
    def _hash_embed(text: str, dim: int = 384) -> list[float]:
        h = hashlib.sha256(text.encode()).hexdigest()
        values = []
        for i in range(0, len(h), 2):
            if len(values) >= dim:
                break
            values.append((int(h[i:i+2], 16) - 128) / 128.0)
        while len(values) < dim:
            h = hashlib.sha256(h.encode()).hexdigest()
            for i in range(0, len(h), 2):
                if len(values) >= dim:
                    break
                values.append((int(h[i:i+2], 16) - 128) / 128.0)
        return values


embedding_service = EmbeddingService()
