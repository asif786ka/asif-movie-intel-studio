import os
import glob
from app.core.logging import get_logger
from app.services.ingestion_service import ingestion_service
from app.models.schemas_upload import DocumentMetadata
from app.db.vector_store import vector_store

logger = get_logger(__name__)

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data", "docs")

DOC_METADATA = {
    "interstellar_review.txt": DocumentMetadata(
        movie_title="Interstellar",
        source_type="review",
        release_year=2014,
        director="Christopher Nolan",
        tmdb_id=157336,
    ),
    "dune_timeline.txt": DocumentMetadata(
        movie_title="Dune",
        source_type="timeline",
        release_year=2021,
        director="Denis Villeneuve",
        franchise="Dune",
        tmdb_id=438631,
    ),
    "oppenheimer_awards.txt": DocumentMetadata(
        movie_title="Oppenheimer",
        source_type="award_writeup",
        release_year=2023,
        director="Christopher Nolan",
        tmdb_id=872585,
    ),
    "villeneuve_analysis.txt": DocumentMetadata(
        movie_title="Denis Villeneuve Films",
        source_type="analysis",
        director="Denis Villeneuve",
    ),
    "tom_cruise_career.txt": DocumentMetadata(
        movie_title="Tom Cruise Films",
        source_type="analysis",
        actor="Tom Cruise",
    ),
}


async def seed_sample_documents():
    existing_count = vector_store.count()
    if existing_count > 0:
        logger.info(f"Vector store already has {existing_count} documents, skipping seed")
        return

    if not os.path.exists(DOCS_DIR):
        logger.warning(f"Sample docs directory not found: {DOCS_DIR}")
        return

    doc_files = glob.glob(os.path.join(DOCS_DIR, "*.txt"))
    if not doc_files:
        logger.warning("No sample documents found")
        return

    logger.info(f"Seeding {len(doc_files)} sample documents...")

    for filepath in doc_files:
        filename = os.path.basename(filepath)
        metadata = DOC_METADATA.get(filename, DocumentMetadata(source_type="document"))

        try:
            await ingestion_service.ingest_file(filepath, metadata)
            logger.info(f"Seeded: {filename}")
        except Exception as e:
            logger.error(f"Failed to seed {filename}: {e}")

    logger.info(f"Seeding complete. Total chunks: {vector_store.count()}")
