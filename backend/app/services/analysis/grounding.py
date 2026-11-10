import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.models.analysis import AnalysisRun
from backend.app.models.document import Document, DocumentChunk
from backend.app.schemas.retrieval import SourceResult
from backend.app.services.retrieval.search import search_chunks


NOT_EXPLICIT = "Not explicitly mentioned in the uploaded paper."


def require_documents(session: Session, document_ids: list[str]) -> list[Document]:
    documents = list(session.scalars(select(Document).where(Document.id.in_(document_ids))).all())
    by_id = {document.id: document for document in documents}
    missing = [document_id for document_id in document_ids if document_id not in by_id]
    if missing:
        raise HTTPException(status_code=404, detail="One or more documents were not found.")
    unprocessed = [document for document in documents if document.status not in {"processed", "processed_with_warnings"}]
    if unprocessed:
        raise HTTPException(status_code=409, detail="One or more documents are not ready for analysis.")
    return [by_id[document_id] for document_id in document_ids]


def collect_evidence(
    session: Session,
    settings: Settings,
    document_ids: list[str],
    queries: list[str],
    per_query: int = 3,
) -> dict[str, SourceResult]:
    evidence: dict[str, SourceResult] = {}
    for query in queries:
        matches, _mode, _fallback = search_chunks(session, settings, query, per_query, document_ids)
        for chunk, score in matches:
            if chunk.id not in evidence:
                evidence[chunk.id] = SourceResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document.id,
                    filename=chunk.document.original_filename,
                    page_number=chunk.page_number,
                    section_heading=chunk.section_heading,
                    excerpt=chunk.content,
                    score=score,
                )
    return evidence


def context_block(sources: dict[str, SourceResult]) -> str:
    return "\n\n".join(
        f"[chunk_id={source.chunk_id}] {source.filename}, page {source.page_number}"
        f"{f', section {source.section_heading}' if source.section_heading else ''}\n{source.excerpt}"
        for source in sources.values()
    )


def supported_sources(chunk_ids: list[str], sources: dict[str, SourceResult]) -> list[SourceResult] | None:
    if not chunk_ids or any(chunk_id not in sources for chunk_id in chunk_ids):
        return None
    return [sources[chunk_id] for chunk_id in dict.fromkeys(chunk_ids)]


def save_analysis_run(
    session: Session,
    kind: str,
    document_ids: list[str],
    request_data: dict[str, Any],
    result_data: dict[str, Any],
) -> str:
    run = AnalysisRun(
        kind=kind,
        document_ids=document_ids,
        request_data=request_data,
        result_data=result_data,
    )
    session.add(run)
    session.commit()
    return run.id


def source_documents(sources: dict[str, SourceResult]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for chunk_id, source in sources.items():
        result.setdefault(source.document_id, set()).add(chunk_id)
    return result


def context_json(sources: dict[str, SourceResult]) -> str:
    return json.dumps([source.model_dump(mode="json") for source in sources.values()], ensure_ascii=False)
