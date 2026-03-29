import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tmdb_service import tmdb_service


@pytest.mark.asyncio
async def test_search_movie_seed():
    results = await tmdb_service.search_movie("Interstellar")
    assert len(results) > 0
    assert results[0].title == "Interstellar"


@pytest.mark.asyncio
async def test_search_movie_not_found():
    results = await tmdb_service.search_movie("xyznonexistentmovie12345")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_movie_details_seed():
    details = await tmdb_service.get_movie_details(157336)
    assert details is not None
    assert details.title == "Interstellar"
    assert details.runtime == 169


@pytest.mark.asyncio
async def test_get_movie_credits_seed():
    credits = await tmdb_service.get_movie_credits(157336)
    assert credits is not None
    assert len(credits.cast) > 0
    assert any(c.name == "Matthew McConaughey" for c in credits.cast)


@pytest.mark.asyncio
async def test_get_similar_movies_seed():
    similar = await tmdb_service.get_similar_movies(157336)
    assert len(similar) > 0


@pytest.mark.asyncio
async def test_get_movie_brief_seed():
    brief = await tmdb_service.get_movie_brief(157336)
    assert brief is not None
    assert brief.title == "Interstellar"
    assert brief.director == "Christopher Nolan"
    assert brief.year == "2014"
