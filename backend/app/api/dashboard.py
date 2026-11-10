from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.analysis import AnalysisRun
from backend.app.models.document import Document
from backend.app.schemas.dashboard import AnalysisHistoryItem, CountItem, DashboardResponse
from backend.app.schemas.documents import DocumentRead


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(session: Session = Depends(get_db)) -> DashboardResponse:
    documents = list(session.scalars(select(Document).order_by(Document.created_at.desc())).all())
    processed = sum(item.status in {"processed", "processed_with_warnings"} for item in documents)
    failed = sum(item.status == "failed" for item in documents)
    processing = sum(item.status in {"uploaded", "processing"} for item in documents)
    years = Counter(str(item.publication_year) for item in documents if item.publication_year)
    keywords = Counter(keyword.strip() for item in documents for keyword in item.keywords if keyword.strip())
    runs = list(session.scalars(select(AnalysisRun).order_by(AnalysisRun.created_at.desc()).limit(12)).all())

    def history_item(run: AnalysisRun) -> AnalysisHistoryItem:
        return AnalysisHistoryItem(id=run.id, kind=run.kind, document_ids=run.document_ids, created_at=run.created_at)

    return DashboardResponse(
        total_documents=len(documents),
        processed_documents=processed,
        failed_documents=failed,
        processing_documents=processing,
        total_chunks=sum(item.chunk_count for item in documents),
        recent_documents=[DocumentRead.model_validate(item) for item in documents[:6]],
        papers_by_year=[CountItem(label=year, count=count) for year, count in sorted(years.items())],
        frequent_keywords=[CountItem(label=keyword, count=count) for keyword, count in keywords.most_common(8)],
        analysis_history=[history_item(run) for run in runs],
        recent_comparisons=[history_item(run) for run in runs if run.kind == "comparison"][:5],
    )
