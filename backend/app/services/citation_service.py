import re
from typing import Optional
from app.core.logging import get_logger
from app.models.schemas_chat import Citation
from app.services.retrieval_service import RetrievedDocument

logger = get_logger(__name__)


class CitationService:
    def extract_citations(self, answer: str, sources: list[RetrievedDocument]) -> list[Citation]:
        citation_pattern = r'\[Source\s*(\d+)\]'
        matches = re.findall(citation_pattern, answer)
        cited_indices = set(int(m) for m in matches)

        citations = []
        for idx in sorted(cited_indices):
            source_idx = idx - 1
            if 0 <= source_idx < len(sources):
                source = sources[source_idx]
                citations.append(Citation(
                    source_index=idx,
                    source_title=source.metadata.get("movie_title", source.metadata.get("filename", f"Source {idx}")),
                    source_type=source.metadata.get("source_type", "document"),
                    chunk_text=source.content[:500],
                    relevance_score=source.score,
                    metadata=source.metadata,
                ))
        return citations

    def validate_citations(self, answer: str, sources: list[RetrievedDocument]) -> tuple[bool, list[str]]:
        issues = []
        citation_pattern = r'\[Source\s*(\d+)\]'
        matches = re.findall(citation_pattern, answer)

        for match in matches:
            idx = int(match) - 1
            if idx < 0 or idx >= len(sources):
                issues.append(f"Citation [Source {match}] references non-existent source")

        if not matches and len(answer) > 200:
            issues.append("Long answer with no citations")

        return len(issues) == 0, issues

    def add_missing_citations(self, answer: str, sources: list[RetrievedDocument]) -> str:
        if not sources:
            return answer
        citation_pattern = r'\[Source\s*\d+\]'
        if not re.search(citation_pattern, answer) and len(answer) > 100:
            source_refs = ", ".join([f"[Source {i+1}]" for i in range(min(len(sources), 3))])
            answer += f"\n\n*Sources: {source_refs}*"
        return answer


citation_service = CitationService()
