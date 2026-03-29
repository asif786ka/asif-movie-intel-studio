import os
import uuid
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.services.embedding_service import embedding_service
from app.db.vector_store import vector_store
from app.db.metadata_store import metadata_store
from app.db.audit_store import audit_store
from app.models.schemas_upload import DocumentMetadata, IngestionStatus

logger = get_logger(__name__)


class IngestionService:
    def __init__(self):
        self.chunk_size = settings.max_chunk_size
        self.chunk_overlap = settings.chunk_overlap
        os.makedirs(settings.upload_dir, exist_ok=True)

    def chunk_text(self, text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            last_period = chunk.rfind(".")
            last_newline = chunk.rfind("\n")
            break_point = max(last_period, last_newline)
            if break_point > chunk_size * 0.3 and end < len(text):
                end = start + break_point + 1
                chunk = text[start:end]
            chunks.append(chunk.strip())
            start = end - overlap
            if start >= len(text):
                break
        return [c for c in chunks if c]

    async def ingest_document(
        self,
        content: str,
        filename: str,
        metadata: DocumentMetadata,
        job_id: Optional[str] = None,
    ) -> str:
        job_id = job_id or str(uuid.uuid4())
        metadata_store.add_upload_job(job_id, filename, "processing")
        audit_store.log("document_upload", details={"filename": filename, "job_id": job_id})

        try:
            chunks = self.chunk_text(content)
            if not chunks:
                metadata_store.update_upload_job(job_id, status="failed", error="No content to ingest")
                return job_id

            ids = []
            documents = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                doc_id = f"{job_id}_{i}"
                ids.append(doc_id)
                documents.append(chunk)
                meta = {
                    "movie_title": metadata.movie_title or "",
                    "source_type": metadata.source_type,
                    "source_url": metadata.source_url or "",
                    "release_year": str(metadata.release_year) if metadata.release_year else "",
                    "actor": metadata.actor or "",
                    "director": metadata.director or "",
                    "franchise": metadata.franchise or "",
                    "tmdb_id": str(metadata.tmdb_id) if metadata.tmdb_id else "",
                    "tenant_id": metadata.tenant_id,
                    "chunk_index": str(i),
                    "filename": filename,
                    "total_chunks": str(len(chunks)),
                }
                metadatas.append(meta)

            embeddings = embedding_service.embed_texts(documents)
            vector_store.add_documents(ids, documents, embeddings, metadatas)

            metadata_store.update_upload_job(
                job_id,
                status="completed",
                chunk_count=len(chunks),
                completed_at=__import__("datetime").datetime.now().isoformat(),
            )
            logger.info(f"Ingested {len(chunks)} chunks from {filename}")
            return job_id

        except Exception as e:
            logger.error(f"Ingestion failed for {filename}: {e}")
            metadata_store.update_upload_job(job_id, status="failed", error=str(e))
            return job_id

    async def ingest_file(self, filepath: str, metadata: DocumentMetadata) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        filename = os.path.basename(filepath)
        return await self.ingest_document(content, filename, metadata)


ingestion_service = IngestionService()
