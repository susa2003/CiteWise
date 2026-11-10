from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.schemas.retrieval import SearchRequest, SearchResponse, SourceResult
from backend.app.services.retrieval.search import search_chunks


router = APIRouter(tags=["retrieval"])


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, session: Session = Depends(get_db)) -> SearchResponse:
    results, mode, fallback = search_chunks(
        session,
        get_settings(),
        request.query,
        limit=request.top_k,
        document_ids=request.document_ids,
    )
    sources = [
        SourceResult(
            chunk_id=chunk.id,
            document_id=chunk.document.id,
            filename=chunk.document.original_filename,
            page_number=chunk.page_number,
            section_heading=chunk.section_heading,
            excerpt=chunk.content,
            score=score,
        )
        for chunk, score in results
    ]
    return SearchResponse(
        query=request.query,
        retrieval_mode=mode,
        semantic_fallback=fallback,
        sufficient_evidence=bool(sources),
        results=sources,
    )
