from hashlib import sha256
import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from backend.app.core.config import Settings
from backend.app.models.document import Document, DocumentChunk, DocumentPage
from backend.app.services.documents.extractor import extract_pdf
from backend.app.services.documents.validation import has_pdf_signature, safe_original_filename
from backend.app.services.retrieval.semantic_store import upsert_chunks


class UploadRejected(ValueError):
    """An upload failed a user-correctable file validation rule."""


async def ingest_pdf(upload: UploadFile, session: Session, settings: Settings) -> tuple[Document, bool]:
    filename = safe_original_filename(upload.filename)
    if Path(filename).suffix.lower() != ".pdf":
        raise UploadRejected("Only PDF files can be uploaded.")
    if upload.content_type and upload.content_type not in {"application/pdf", "application/octet-stream"}:
        raise UploadRejected("The uploaded file must have a PDF content type.")

    upload_dir = settings.storage_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    temporary_path = upload_dir / f".{token}.upload"
    digest = sha256()
    prefix = bytearray()
    byte_count = 0
    try:
        with temporary_path.open("wb") as destination:
            while block := await upload.read(1024 * 1024):
                byte_count += len(block)
                if byte_count > settings.max_upload_bytes:
                    raise UploadRejected(f"File exceeds the {settings.max_upload_mb} MB upload limit.")
                if len(prefix) < 1024:
                    prefix.extend(block[: 1024 - len(prefix)])
                digest.update(block)
                destination.write(block)
        if byte_count == 0:
            raise UploadRejected("The uploaded file is empty.")
        if not has_pdf_signature(bytes(prefix)):
            raise UploadRejected("The file does not contain a valid PDF header.")

        file_hash = digest.hexdigest()
        existing = session.scalar(select(Document).where(Document.sha256 == file_hash))
        if existing:
            temporary_path.unlink(missing_ok=True)
            return existing, True

        document_id = uuid4().hex
        relative_path = f"uploads/{document_id}.pdf"
        destination_path = settings.storage_dir / relative_path
        os.replace(temporary_path, destination_path)
        document = Document(
            id=document_id,
            original_filename=filename,
            storage_path=relative_path,
            sha256=file_hash,
            file_size=byte_count,
            status="processing",
        )
        session.add(document)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            existing = session.scalar(select(Document).where(Document.sha256 == file_hash))
            destination_path.unlink(missing_ok=True)
            if existing:
                return existing, True
            raise

        try:
            extracted = await run_in_threadpool(extract_pdf, destination_path, settings.ocr_enabled)
            document.title = extracted.metadata.get("title")
            document.authors = extracted.metadata.get("authors", [])
            document.abstract = extracted.metadata.get("abstract")
            document.publication_year = extracted.metadata.get("publication_year")
            document.doi = extracted.metadata.get("doi")
            document.keywords = extracted.metadata.get("keywords", [])
            document.references = extracted.metadata.get("references", [])
            document.metadata_sources = extracted.metadata_sources
            document.page_count = len(extracted.pages)
            document.warnings = extracted.warnings

            page_records: dict[int, DocumentPage] = {}
            for page_data in extracted.pages:
                page = DocumentPage(
                    document_id=document.id,
                    page_number=page_data.page_number,
                    text=page_data.text,
                    section_heading=page_data.section_heading,
                    extraction_method=page_data.extraction_method,
                    warnings=page_data.warnings,
                )
                session.add(page)
                page_records[page_data.page_number] = page
            session.flush()

            for chunk_data in extracted.chunks:
                page_number = int(chunk_data["page_number"])
                content = str(chunk_data["content"])
                session.add(DocumentChunk(
                    document_id=document.id,
                    page_id=page_records[page_number].id,
                    page_number=page_number,
                    chunk_index=int(chunk_data["chunk_index"]),
                    section_heading=chunk_data["section_heading"],
                    content=content,
                    content_length=len(content),
                ))
            document.chunk_count = len(extracted.chunks)
            document.status = "processed_with_warnings" if extracted.warnings else "processed"
            session.commit()

            if settings.embedding_provider == "sentence_transformers":
                try:
                    chunks = list(session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).all())
                    await run_in_threadpool(upsert_chunks, chunks, document.original_filename)
                    for chunk in chunks:
                        chunk.vector_id = chunk.id
                    session.commit()
                except Exception:
                    session.rollback()
                    document = session.get(Document, document_id)
                    document.warnings = [*document.warnings, "Semantic indexing failed; keyword search remains available."]
                    document.status = "processed_with_warnings"
                    session.commit()
        except Exception:
            session.rollback()
            document = session.get(Document, document_id)
            if document:
                document.status = "failed"
                document.processing_error = "The PDF was saved, but text extraction could not be completed."
                session.commit()
        return session.get(Document, document_id), False
    except UploadRejected:
        temporary_path.unlink(missing_ok=True)
        raise
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()
