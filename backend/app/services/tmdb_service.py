import httpx
import json
import os
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas_movie import (
    MovieSearchResult, MovieDetails, MovieCredits,
    CastMember, CrewMember, MovieBrief,
)

logger = get_logger(__name__)

SEED_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "seed_movies.json")


def _load_seed_movies() -> list[dict]:
    try:
        with open(SEED_DATA_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


SEED_MOVIES = _load_seed_movies()


class TMDBService:
    def __init__(self):
        self.api_key = settings.tmdb_api_key
        self.base_url = settings.tmdb_base_url
        self.image_base = "https://image.tmdb.org/t/p/w500"

    @property
    def _has_api_key(self) -> bool:
        return bool(self.api_key)

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        if not self._has_api_key:
            raise ValueError("TMDB API key not configured")
        params = params or {}
        params["api_key"] = self.api_key
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}{endpoint}", params=params, timeout=10.0)
            resp.raise_for_status()
            return resp.json()

    async def search_movie(self, query: str, page: int = 1) -> list[MovieSearchResult]:
        if not self._has_api_key:
            return self._search_seed(query)
        try:
            data = await self._get("/search/movie", {"query": query, "page": page})
            return [MovieSearchResult(**r) for r in data.get("results", [])]
        except Exception as e:
            logger.warning(f"TMDB search failed, using seed data: {e}")
            return self._search_seed(query)

    async def get_movie_details(self, movie_id: int) -> Optional[MovieDetails]:
        if not self._has_api_key:
            return self._get_seed_details(movie_id)
        try:
            data = await self._get(f"/movie/{movie_id}")
            return MovieDetails(**data)
        except Exception as e:
            logger.warning(f"TMDB details failed, using seed data: {e}")
            return self._get_seed_details(movie_id)

    async def get_movie_credits(self, movie_id: int) -> Optional[MovieCredits]:
        if not self._has_api_key:
            return self._get_seed_credits(movie_id)
        try:
            data = await self._get(f"/movie/{movie_id}/credits")
            cast = [CastMember(**c) for c in data.get("cast", [])[:20]]
            crew = [CrewMember(**c) for c in data.get("crew", [])[:20]]
            return MovieCredits(movie_id=movie_id, cast=cast, crew=crew)
        except Exception as e:
            logger.warning(f"TMDB credits failed, using seed data: {e}")
            return self._get_seed_credits(movie_id)

    async def get_similar_movies(self, movie_id: int) -> list[MovieSearchResult]:
        if not self._has_api_key:
            return self._get_seed_similar(movie_id)
        try:
            data = await self._get(f"/movie/{movie_id}/similar")
            return [MovieSearchResult(**r) for r in data.get("results", [])[:10]]
        except Exception as e:
            logger.warning(f"TMDB similar failed, using seed data: {e}")
            return self._get_seed_similar(movie_id)

    async def get_movie_brief(self, movie_id: int) -> Optional[MovieBrief]:
        details = await self.get_movie_details(movie_id)
        if not details:
            return None
        credits = await self.get_movie_credits(movie_id)
        director = ""
        if credits:
            directors = [c.name for c in credits.crew if c.job == "Director"]
            director = directors[0] if directors else ""
        return MovieBrief(
            id=details.id,
            title=details.title,
            year=details.release_date[:4] if details.release_date else "",
            rating=details.vote_average,
            genres=[g["name"] for g in details.genres],
            director=director,
            poster_url=f"{self.image_base}{details.poster_path}" if details.poster_path else None,
        )

    def _search_seed(self, query: str) -> list[MovieSearchResult]:
        query_lower = query.lower()
        results = []
        for m in SEED_MOVIES:
            if query_lower in m.get("title", "").lower() or query_lower in m.get("overview", "").lower():
                results.append(MovieSearchResult(**m))
        return results[:20]

    def _get_seed_details(self, movie_id: int) -> Optional[MovieDetails]:
        for m in SEED_MOVIES:
            if m.get("id") == movie_id:
                return MovieDetails(**m)
        return None

    def _get_seed_credits(self, movie_id: int) -> Optional[MovieCredits]:
        for m in SEED_MOVIES:
            if m.get("id") == movie_id:
                cast = [CastMember(**c) for c in m.get("cast", [])]
                crew = [CrewMember(**c) for c in m.get("crew", [])]
                return MovieCredits(movie_id=movie_id, cast=cast, crew=crew)
        return None

    def _get_seed_similar(self, movie_id: int) -> list[MovieSearchResult]:
        target = None
        for m in SEED_MOVIES:
            if m.get("id") == movie_id:
                target = m
                break
        if not target:
            return []
        target_genres = set(target.get("genre_ids", []))
        similar = []
        for m in SEED_MOVIES:
            if m["id"] != movie_id and set(m.get("genre_ids", [])) & target_genres:
                similar.append(MovieSearchResult(**m))
        return similar[:10]


tmdb_service = TMDBService()
