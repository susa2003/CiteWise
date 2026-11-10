from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.models.document import Document, DocumentChunk
from backend.app.services.retrieval.bm25 import rank_bm25
from backend.app.services.retrieval.semantic_store import query_chunks


def search_chunks(
    session: Session,
    settings: Settings,
    query: str,
    limit: int = 8,
    document_ids: list[str] | None = None,
) -> tuple[list[tuple[DocumentChunk, float]], str, bool]:
    statement = select(DocumentChunk).join(Document).where(Document.status.in_(["processed", "processed_with_warnings"]))
    if document_ids:
        statement = statement.where(Document.id.in_(document_ids))
    chunks = list(session.scalars(statement).all())

    keyword_results = rank_bm25(query, chunks, limit=max(limit * 4, 20))
    if not settings.embedding_provider or settings.embedding_provider == "none":
        return keyword_results[:limit], "keyword", False

    try:
        semantic_ids = query_chunks(query, limit=max(limit * 4, 20), document_ids=document_ids)
    except (ImportError, RuntimeError, OSError):
        # Keep the application usable if the optional local model or vector store is absent.
        return keyword_results[:limit], "keyword_fallback", True
    if not semantic_ids:
        return keyword_results[:limit], "keyword_fallback", True

    chunk_by_id = {chunk.id: chunk for chunk in chunks}
    ranked_ids: list[str] = []
    for chunk, _ in keyword_results:
        ranked_ids.append(chunk.id)
    for chunk_id, _distance in semantic_ids:
        if chunk_id in chunk_by_id and chunk_id not in ranked_ids:
            ranked_ids.append(chunk_id)

    keyword_rank = {chunk.id: index + 1 for index, (chunk, _score) in enumerate(keyword_results)}
    semantic_rank = {chunk_id: index + 1 for index, (chunk_id, _distance) in enumerate(semantic_ids)}
    fused: list[tuple[DocumentChunk, float]] = []
    for chunk_id in ranked_ids:
        reciprocal_score = 0.0
        if chunk_id in keyword_rank:
            reciprocal_score += 1 / (60 + keyword_rank[chunk_id])
        if chunk_id in semantic_rank:
            reciprocal_score += 1 / (60 + semantic_rank[chunk_id])
        fused.append((chunk_by_id[chunk_id], reciprocal_score))
    fused.sort(key=lambda item: (-item[1], item[0].id))
    return fused[:limit], "hybrid", False
