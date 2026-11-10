from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    document_ids: list[str] | None = Field(default=None, max_length=100)
    top_k: int = Field(default=8, ge=1, le=20)


class SourceResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    section_heading: str | None
    excerpt: str
    score: float


class SearchResponse(BaseModel):
    query: str
    retrieval_mode: str
    semantic_fallback: bool
    sufficient_evidence: bool
    results: list[SourceResult]
