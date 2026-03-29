import os
import json
import numpy as np
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Lightweight vector store using numpy for cosine similarity.
    
    Stores documents, embeddings, and metadata in memory with optional
    JSON file persistence. No external dependencies like ChromaDB needed.
    """

    def __init__(self):
        self._documents: list[str] = []
        self._embeddings: list[list[float]] = []
        self._metadatas: list[dict] = []
        self._ids: list[str] = []
        self._initialized = False
        self._persist_path = os.path.abspath(
            os.path.join(settings.chroma_persist_dir, "store.json")
        )

    def _ensure_initialized(self):
        if self._initialized:
            return
        self._initialized = True
        os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
        if os.path.exists(self._persist_path):
            try:
                with open(self._persist_path, "r") as f:
                    data = json.load(f)
                self._ids = data.get("ids", [])
                self._documents = data.get("documents", [])
                self._embeddings = data.get("embeddings", [])
                self._metadatas = data.get("metadatas", [])
                logger.info(f"Vector store loaded from {self._persist_path}, docs: {len(self._ids)}")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
        else:
            logger.info("Vector store initialized (empty)")

    def _persist(self):
        try:
            with open(self._persist_path, "w") as f:
                json.dump({
                    "ids": self._ids,
                    "documents": self._documents,
                    "embeddings": self._embeddings,
                    "metadatas": self._metadatas,
                }, f)
        except Exception as e:
            logger.error(f"Failed to persist vector store: {e}")

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ):
        self._ensure_initialized()
        for i, doc_id in enumerate(ids):
            if doc_id in self._ids:
                idx = self._ids.index(doc_id)
                self._documents[idx] = documents[i]
                self._embeddings[idx] = embeddings[i]
                self._metadatas[idx] = metadatas[i]
            else:
                self._ids.append(doc_id)
                self._documents.append(documents[i])
                self._embeddings.append(embeddings[i])
                self._metadatas.append(metadatas[i])
        self._persist()
        logger.info(f"Added {len(ids)} documents to vector store")

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: Optional[dict] = None,
    ) -> dict:
        self._ensure_initialized()
        if not self._embeddings:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        query_vec = query_vec / query_norm

        indices = list(range(len(self._ids)))
        if where:
            filtered = []
            for i in indices:
                meta = self._metadatas[i]
                match = True
                for key, val in where.items():
                    if key.startswith("$"):
                        continue
                    if meta.get(key) != val:
                        match = False
                        break
                if match:
                    filtered.append(i)
            indices = filtered

        if not indices:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        doc_vecs = np.array([self._embeddings[i] for i in indices], dtype=np.float32)
        norms = np.linalg.norm(doc_vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1
        doc_vecs = doc_vecs / norms

        similarities = doc_vecs @ query_vec
        distances = 1.0 - similarities

        top_k = min(n_results, len(indices))
        top_indices = np.argsort(distances)[:top_k]

        result_ids = [self._ids[indices[i]] for i in top_indices]
        result_docs = [self._documents[indices[i]] for i in top_indices]
        result_metas = [self._metadatas[indices[i]] for i in top_indices]
        result_dists = [float(distances[i]) for i in top_indices]

        return {
            "ids": [result_ids],
            "documents": [result_docs],
            "metadatas": [result_metas],
            "distances": [result_dists],
        }

    def count(self) -> int:
        try:
            self._ensure_initialized()
            return len(self._ids)
        except Exception:
            return 0

    def delete_collection(self):
        self._ensure_initialized()
        self._ids.clear()
        self._documents.clear()
        self._embeddings.clear()
        self._metadatas.clear()
        self._persist()

    def get_all_metadata(self) -> list[dict]:
        self._ensure_initialized()
        return list(self._metadatas)


vector_store = VectorStore()
