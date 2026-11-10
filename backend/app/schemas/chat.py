from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.retrieval import SourceResult


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    conversation_id: str | None = None
    document_ids: list[str] | None = Field(default=None, max_length=100)
    top_k: int = Field(default=8, ge=1, le=20)


class ProposedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=2, max_length=2000)
    interpretation: bool = False
    chunk_ids: list[str] = Field(min_length=1, max_length=8)


class ProposedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    insufficient_evidence: bool
    claims: list[ProposedClaim] = Field(default_factory=list, max_length=30)


class ValidatedClaim(BaseModel):
    text: str
    interpretation: bool
    citations: list[SourceResult]


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    mode: str
    evidence_found: bool
    insufficient_evidence: bool
    claims: list[ValidatedClaim]
    sources: list[SourceResult]


class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class StoredCitation(BaseModel):
    chunk_id: str | None
    document_id: str
    filename: str
    page_number: int
    excerpt: str
    citation_type: str


class StoredMessage(BaseModel):
    id: str
    role: str
    content: str
    answer_mode: str | None
    insufficient_evidence: bool | None
    created_at: str
    citations: list[StoredCitation]


class ConversationRead(BaseModel):
    id: str
    title: str
    messages: list[StoredMessage]
