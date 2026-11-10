from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.models.document import Document, DocumentPage
from backend.app.schemas.documents import (
    DocumentListResponse,
    DocumentRead,
    PageRead,
    UploadBatchResponse,
    UploadItemResult,
)
from backend.app.services.documents.ingestion import UploadRejected, ingest_pdf
from backend.app.services.documents.validation import resolve_storage_path
from backend.app.services.retrieval.semantic_store import delete_document_vectors


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=UploadBatchResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_db),
) -> UploadBatchResponse:
    results: list[UploadItemResult] = []
    for upload in files:
        filename = upload.filename or "research-paper.pdf"
        try:
            document, duplicate = await ingest_pdf(upload, session, get_settings())
            results.append(UploadItemResult(
                filename=filename,
                document=DocumentRead.model_validate(document),
                duplicate=duplicate,
            ))
        except UploadRejected as exc:
            results.append(UploadItemResult(filename=filename, error=str(exc)))
        except Exception:
            results.append(UploadItemResult(filename=filename, error="Upload could not be stored. Please try again."))
    return UploadBatchResponse(results=results)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    limit: int = 25,
    offset: int = 0,
    session: Session = Depends(get_db),
) -> DocumentListResponse:
    if limit < 1 or limit > 100 or offset < 0:
        raise HTTPException(status_code=422, detail="Limit must be 1–100 and offset cannot be negative.")
    total = session.scalar(select(func.count()).select_from(Document)) or 0
    items = session.scalars(
        select(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return DocumentListResponse(items=[DocumentRead.model_validate(item) for item in items], total=total, limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: str, session: Session = Depends(get_db)) -> DocumentRead:
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentRead.model_validate(document)


@router.get("/{document_id}/pages/{page_number}", response_model=PageRead)
def get_document_page(document_id: str, page_number: int, session: Session = Depends(get_db)) -> PageRead:
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    page = session.scalar(select(DocumentPage).where(
        DocumentPage.document_id == document_id,
        DocumentPage.page_number == page_number,
    ))
    if not page:
        raise HTTPException(status_code=404, detail="Page not found.")
    return PageRead(
        document_id=document.id,
        original_filename=document.original_filename,
        page_number=page.page_number,
        section_heading=page.section_heading,
        extraction_method=page.extraction_method,
        warnings=page.warnings,
        text=page.text,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, session: Session = Depends(get_db)) -> None:
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        delete_document_vectors(document_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="The document index could not be removed.") from exc
    try:
        stored_path = resolve_storage_path(get_settings().storage_dir, document.storage_path)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Stored document path is invalid.") from exc
    try:
        stored_path.unlink(missing_ok=True)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="The stored PDF could not be removed.") from exc
    session.delete(document)
    session.commit()
