from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    status: str
    file_size: int
    title: str | None
    authors: list[str]
    abstract: str | None
    publication_year: int | None
    doi: str | None
    keywords: list[str]
    references: list[str]
    metadata_sources: dict[str, str]
    page_count: int
    chunk_count: int
    warnings: list[str]
    processing_error: str | None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentRead]
    total: int
    limit: int
    offset: int


class UploadItemResult(BaseModel):
    filename: str
    document: DocumentRead | None = None
    duplicate: bool = False
    error: str | None = None


class UploadBatchResponse(BaseModel):
    results: list[UploadItemResult]


class PageRead(BaseModel):
    document_id: str
    original_filename: str
    page_number: int
    section_heading: str | None
    extraction_method: str
    warnings: list[str]
    text: str
