from pydantic import BaseModel, Field
from typing import Optional


class MovieSearchResult(BaseModel):
    id: int
    title: str
    overview: str = ""
    release_date: str = ""
    vote_average: float = 0.0
    vote_count: int = 0
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    genre_ids: list[int] = []
    popularity: float = 0.0


class MovieDetails(BaseModel):
    id: int
    title: str
    overview: str = ""
    release_date: str = ""
    vote_average: float = 0.0
    vote_count: int = 0
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    genres: list[dict] = []
    runtime: Optional[int] = None
    budget: int = 0
    revenue: int = 0
    tagline: str = ""
    status: str = ""
    production_companies: list[dict] = []
    spoken_languages: list[dict] = []


class CastMember(BaseModel):
    id: int
    name: str
    character: str = ""
    profile_path: Optional[str] = None
    order: int = 0


class CrewMember(BaseModel):
    id: int
    name: str
    job: str = ""
    department: str = ""
    profile_path: Optional[str] = None


class MovieCredits(BaseModel):
    movie_id: int
    cast: list[CastMember] = []
    crew: list[CrewMember] = []


class MovieBrief(BaseModel):
    id: int
    title: str
    year: str = ""
    rating: float = 0.0
    genres: list[str] = []
    director: str = ""
    poster_url: Optional[str] = None


class CompareRequest(BaseModel):
    movie_ids: list[int] = Field(..., min_length=2, max_length=5)
    dimensions: list[str] = Field(
        default=["themes", "critic_reception", "audience_reception", "awards", "timeline", "cast_and_director"]
    )


class ComparisonSection(BaseModel):
    dimension: str
    content: str
    citations: list[dict] = []


class CompareResponse(BaseModel):
    movies: list[MovieBrief] = []
    summary: str = ""
    themes: Optional[ComparisonSection] = None
    critic_reception: Optional[ComparisonSection] = None
    audience_reception: Optional[ComparisonSection] = None
    awards: Optional[ComparisonSection] = None
    timeline: Optional[ComparisonSection] = None
    cast_and_director: Optional[ComparisonSection] = None
    sections: list[ComparisonSection] = []
    citations: list[dict] = []
    confidence: float = 0.0
    trace_id: str = ""
    latency_ms: float = 0.0
