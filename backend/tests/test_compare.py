import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.compare_service import compare_service


@pytest.mark.asyncio
async def test_compare_two_movies():
    result = await compare_service.compare_movies(
        movie_ids=[157336, 438631],
        dimensions=["themes", "critic_reception"],
    )
    assert len(result.movies) == 2
    assert result.movies[0].title == "Interstellar"
    assert result.movies[1].title == "Dune"
    assert result.trace_id != ""
    assert result.latency_ms > 0
    assert len(result.sections) == 2


@pytest.mark.asyncio
async def test_compare_nonexistent_movies():
    result = await compare_service.compare_movies(
        movie_ids=[999999999, 999999998],
        dimensions=["themes"],
    )
    assert len(result.movies) == 0
