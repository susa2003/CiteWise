from datetime import datetime

from pydantic import BaseModel

from backend.app.schemas.documents import DocumentRead


class CountItem(BaseModel):
    label: str
    count: int


class AnalysisHistoryItem(BaseModel):
    id: str
    kind: str
    document_ids: list[str]
    created_at: datetime


class DashboardResponse(BaseModel):
    total_documents: int
    processed_documents: int
    failed_documents: int
    processing_documents: int
    total_chunks: int
    recent_documents: list[DocumentRead]
    papers_by_year: list[CountItem]
    frequent_keywords: list[CountItem]
    analysis_history: list[AnalysisHistoryItem]
    recent_comparisons: list[AnalysisHistoryItem]
