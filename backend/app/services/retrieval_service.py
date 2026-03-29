"""
RetrievalService — Vector similarity search against ChromaDB.

Architecture Note (Senior AI Architect):
  This service is the RAG "R" — it converts natural language queries into
  embedding vectors and searches the ChromaDB collection for similar documents.

  Retrieval Pipeline:
    1. Query → embedding_service.embed_text(query) → 1536-dim vector
    2. Vector → ChromaDB cosine similarity search → top_k candidates
    3. Candidates → scored by (1 - distance) → sorted by relevance
    4. Optional metadata filters (movie_title, source_type) for scoped retrieval

  Scalability Considerations:
    - ChromaDB supports persistent storage and millions of documents
    - Embedding calls are the main latency bottleneck (consider caching)
    - For production scale: swap ChromaDB for Pinecone/Weaviate/Qdrant
    - top_k=10 balances recall vs. context window size
"""

from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.services.embedding_service import embedding_service
from app.db.vector_store import vector_store

logger = get_logger(__name__)


class RetrievedDocument:
    """Represents a single document retrieved from the vector store.

    Attributes:
        content: The document text chunk
        metadata: Source metadata (movie_title, source_type, director, etc.)
        score: Relevance score (1.0 - cosine distance), range [0, 1]
        doc_id: Unique document chunk identifier in ChromaDB
    """

    def __init__(self, content: str, metadata: dict, score: float, doc_id: str = ""):
        self.content = content
        self.metadata = metadata
        self.score = score
        self.doc_id = doc_id

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
            "doc_id": self.doc_id,
        }


class RetrievalService:
    """Handles all vector similarity search operations against ChromaDB."""

    def __init__(self):
        self.top_k = settings.top_k_retrieval

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> list[RetrievedDocument]:
        """Retrieve documents from ChromaDB by embedding similarity.

        Args:
            query: Natural language search query
            top_k: Maximum number of results (default from settings)
            filters: Optional metadata filters (e.g., {"movie_title": "Inception"})

        Returns:
            List of RetrievedDocument sorted by descending relevance score.
        """
        top_k = top_k or self.top_k

        # Convert query text to embedding vector
        query_embedding = embedding_service.embed_text(query)

        # Build ChromaDB where clause from metadata filters
        where = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if value:
                    conditions.append({key: {"$eq": str(value)}})
            if len(conditions) == 1:
                where = conditions[0]
            elif len(conditions) > 1:
                where = {"$and": conditions}

        # Execute vector similarity search
        results = vector_store.query(
            query_embedding=query_embedding,
            n_results=top_k,
            where=where,
        )

        # Convert ChromaDB results to RetrievedDocument objects
        documents = []
        if results and results.get("documents"):
            for i, doc_list in enumerate(results["documents"]):
                for j, doc in enumerate(doc_list):
                    metadata = results["metadatas"][i][j] if results.get("metadatas") else {}
                    distance = results["distances"][i][j] if results.get("distances") else 1.0
                    # Convert cosine distance to similarity score
                    score = 1.0 - distance
                    doc_id = results["ids"][i][j] if results.get("ids") else ""
                    documents.append(RetrievedDocument(
                        content=doc,
                        metadata=metadata,
                        score=score,
                        doc_id=doc_id,
                    ))

        # Sort by relevance score (highest first) and trim to top_k
        documents.sort(key=lambda d: d.score, reverse=True)
        return documents[:top_k]

    async def retrieve_by_movie(self, movie_title: str, top_k: int = 5) -> list[RetrievedDocument]:
        """Retrieve documents filtered by a specific movie title."""
        return await self.retrieve(movie_title, top_k=top_k, filters={"movie_title": movie_title})

    async def retrieve_by_source_type(self, query: str, source_type: str, top_k: int = 5) -> list[RetrievedDocument]:
        """Retrieve documents filtered by source type (review, analysis, interview, etc.)."""
        return await self.retrieve(query, top_k=top_k, filters={"source_type": source_type})


retrieval_service = RetrievalService()
