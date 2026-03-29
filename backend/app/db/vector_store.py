import os
import chromadb
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    def __init__(self):
        self._client = None
        self._collection = None

    def _ensure_initialized(self):
        if self._collection is not None:
            return
        try:
            persist_dir = os.path.abspath(settings.chroma_persist_dir)
            os.makedirs(persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name="movie_documents",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB initialized at {persist_dir}, docs: {self._collection.count()}")
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise

    @property
    def collection(self):
        self._ensure_initialized()
        return self._collection

    @property
    def client(self):
        self._ensure_initialized()
        return self._client

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ):
        self._ensure_initialized()
        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(ids)} documents to vector store")

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: Optional[dict] = None,
    ) -> dict:
        self._ensure_initialized()
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        return self._collection.query(**kwargs)

    def count(self) -> int:
        try:
            self._ensure_initialized()
            return self._collection.count()
        except Exception:
            return 0

    def delete_collection(self):
        self._ensure_initialized()
        self._client.delete_collection("movie_documents")
        self._collection = self._client.get_or_create_collection(
            name="movie_documents",
            metadata={"hnsw:space": "cosine"},
        )

    def get_all_metadata(self) -> list[dict]:
        self._ensure_initialized()
        result = self._collection.get(include=["metadatas"])
        return result.get("metadatas", [])


vector_store = VectorStore()
