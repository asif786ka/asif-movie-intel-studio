import time
import uuid
from app.core.logging import get_logger
from app.core.prompts import COMPARISON_PROMPT, SYSTEM_PROMPT
from app.services.tmdb_service import tmdb_service
from app.services.retrieval_service import retrieval_service
from app.services.rerank_service import rerank_service
from app.services.citation_service import citation_service
from app.services.bedrock_service import llm_provider
from app.models.schemas_movie import CompareResponse, ComparisonSection, MovieBrief

logger = get_logger(__name__)


class CompareService:
    async def compare_movies(self, movie_ids: list[int], dimensions: list[str]) -> CompareResponse:
        start_time = time.time()
        trace_id = str(uuid.uuid4())[:12]

        movies = []
        tmdb_context_parts = []
        for mid in movie_ids:
            brief = await tmdb_service.get_movie_brief(mid)
            if brief:
                movies.append(brief)
                tmdb_context_parts.append(
                    f"Movie: {brief.title} ({brief.year})\n"
                    f"Rating: {brief.rating}/10\n"
                    f"Genres: {', '.join(brief.genres)}\n"
                    f"Director: {brief.director}"
                )

        movie_titles = [m.title for m in movies]
        all_docs = []
        for title in movie_titles:
            docs = await retrieval_service.retrieve(title, top_k=5)
            all_docs.extend(docs)

        if all_docs:
            query = f"Compare {' and '.join(movie_titles)}"
            all_docs = await rerank_service.rerank(query, all_docs, top_k=10)

        rag_context = "\n\n".join([
            f"[Source {i+1}] ({d.metadata.get('source_type', 'document')} - {d.metadata.get('movie_title', 'Unknown')}):\n{d.content}"
            for i, d in enumerate(all_docs)
        ])

        full_context = "STRUCTURED DATA (TMDB):\n" + "\n\n".join(tmdb_context_parts)
        if rag_context:
            full_context += "\n\nUNSTRUCTURED SOURCES:\n" + rag_context

        prompt = COMPARISON_PROMPT.format(
            context=full_context,
            movies=", ".join(movie_titles),
        )

        answer = await llm_provider.generate(prompt, system_prompt=SYSTEM_PROMPT)

        citations = citation_service.extract_citations(answer, all_docs)

        sections = []
        named_dims = {}
        for dim in dimensions:
            dim_content = self._extract_section(answer, dim)
            section = ComparisonSection(
                dimension=dim,
                content=dim_content or f"Analysis for {dim} dimension.",
                citations=[c.model_dump() for c in citations if dim.lower() in c.chunk_text.lower()],
            )
            sections.append(section)
            named_dims[dim] = section

        latency = (time.time() - start_time) * 1000

        return CompareResponse(
            movies=movies,
            summary=answer[:500] if answer else "Comparison generated.",
            themes=named_dims.get("themes"),
            critic_reception=named_dims.get("critic_reception"),
            audience_reception=named_dims.get("audience_reception"),
            awards=named_dims.get("awards"),
            timeline=named_dims.get("timeline"),
            cast_and_director=named_dims.get("cast_and_director"),
            sections=sections,
            citations=[c.model_dump() for c in citations],
            confidence=0.7 if all_docs else 0.4,
            trace_id=trace_id,
            latency_ms=latency,
        )

    def _extract_section(self, text: str, section_name: str) -> str:
        section_map = {
            "themes": ["theme", "thematic"],
            "critic_reception": ["critic", "critical reception"],
            "audience_reception": ["audience"],
            "awards": ["award", "nomination", "oscar"],
            "timeline": ["timeline", "release", "production"],
            "cast_and_director": ["cast", "director", "actor"],
        }

        keywords = section_map.get(section_name, [section_name])
        lines = text.split("\n")
        section_lines = []
        capturing = False

        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords) and (line.startswith("#") or line.startswith("**")):
                capturing = True
                section_lines.append(line)
                continue
            if capturing:
                if line.startswith("#") or (line.startswith("**") and line.endswith("**")):
                    break
                section_lines.append(line)

        return "\n".join(section_lines).strip() if section_lines else ""


compare_service = CompareService()
