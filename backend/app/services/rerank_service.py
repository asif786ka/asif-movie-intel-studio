from app.core.config import settings
from app.core.logging import get_logger
from app.services.retrieval_service import RetrievedDocument

logger = get_logger(__name__)


class RerankService:
    def __init__(self):
        self.top_k = settings.rerank_top_k

    async def rerank(self, query: str, documents: list[RetrievedDocument], top_k: int | None = None) -> list[RetrievedDocument]:
        top_k = top_k or self.top_k
        if not documents:
            return []

        scored_docs = []
        query_terms = set(query.lower().split())

        for doc in documents:
            doc_terms = set(doc.content.lower().split())
            overlap = len(query_terms & doc_terms)
            term_score = overlap / max(len(query_terms), 1)

            title_match = 0.0
            movie_title = doc.metadata.get("movie_title", "").lower()
            if movie_title and movie_title in query.lower():
                title_match = 0.3

            combined_score = (doc.score * 0.5) + (term_score * 0.3) + title_match + 0.2 * (1.0 / (1 + int(doc.metadata.get("chunk_index", "0"))))
            doc.score = min(combined_score, 1.0)
            scored_docs.append(doc)

        scored_docs.sort(key=lambda d: d.score, reverse=True)
        return scored_docs[:top_k]


rerank_service = RerankService()
