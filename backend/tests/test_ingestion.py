import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ingestion_service import ingestion_service
from app.models.schemas_upload import DocumentMetadata


def test_chunk_text_short():
    text = "This is a short text."
    chunks = ingestion_service.chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_long():
    text = "Word " * 500
    chunks = ingestion_service.chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) > 0


def test_chunk_text_empty():
    chunks = ingestion_service.chunk_text("")
    assert len(chunks) == 1


@pytest.mark.asyncio
async def test_ingest_document():
    content = "Test document about Interstellar. It is a great movie directed by Christopher Nolan."
    metadata = DocumentMetadata(
        movie_title="Interstellar",
        source_type="review",
        director="Christopher Nolan",
    )
    job_id = await ingestion_service.ingest_document(content, "test.txt", metadata)
    assert job_id is not None
