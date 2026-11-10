import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.models.conversation import Citation, Conversation, Message
from backend.app.schemas.chat import ChatRequest, ChatResponse, ProposedAnswer, SourceResult, ValidatedClaim
from backend.app.services.llm.openai_compatible import LLMProviderError, complete_json
from backend.app.services.retrieval.search import search_chunks


router = APIRouter(tags=["chat"])
INSUFFICIENT_TEXT = "The uploaded papers do not contain enough evidence to answer that question."
RETRIEVAL_ONLY_TEXT = "AI answer generation is not configured. The passages below matched your question; no generated answer is being presented."
PROVIDER_ERROR_TEXT = "The configured AI provider could not complete this request. The retrieved paper passages are shown below; no generated answer is being presented."


def _context_message(question: str, sources: list[SourceResult]) -> str:
    excerpt_block = "\n\n".join(
        f"[chunk_id={source.chunk_id}] {source.filename}, page {source.page_number}\n{source.excerpt}"
        for source in sources
    )
    return f"Question: {question}\n\nUploaded-paper evidence excerpts:\n{excerpt_block}"


def validate_proposal(proposal: ProposedAnswer, retrieved: dict[str, SourceResult]) -> list[ValidatedClaim]:
    claims: list[ValidatedClaim] = []
    for proposed in proposal.claims:
        # Drop the full claim if the model supplied even one citation it cannot support.
        if any(chunk_id not in retrieved for chunk_id in proposed.chunk_ids):
            continue
        citations = [retrieved[chunk_id] for chunk_id in dict.fromkeys(proposed.chunk_ids)]
        claims.append(ValidatedClaim(text=proposed.text.strip(), interpretation=proposed.interpretation, citations=citations))
    return claims


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session: Session = Depends(get_db)) -> ChatResponse:
    settings = get_settings()
    conversation: Conversation
    if request.conversation_id:
        conversation = session.get(Conversation, request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        prior_messages = session.scalars(
            select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at.desc()).limit(12)
        ).all()
        prior_messages.reverse()
    else:
        conversation = Conversation(id=uuid4().hex, title=request.question.strip()[:120])
        session.add(conversation)
        session.commit()
        prior_messages = []

    user_message = Message(conversation_id=conversation.id, role="user", content=request.question)
    session.add(user_message)
    session.commit()

    matches, retrieval_mode, fallback = search_chunks(
        session,
        settings,
        request.question,
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
        for chunk, score in matches
    ]
    retrieved = {source.chunk_id: source for source in sources}

    mode = "retrieval_only"
    claims: list[ValidatedClaim] = []
    insufficient = not sources
    if not sources:
        answer = INSUFFICIENT_TEXT
        mode = "insufficient_evidence"
    elif not settings.llm_is_configured:
        answer = RETRIEVAL_ONLY_TEXT
    else:
        history = [{"role": item.role, "content": item.content} for item in prior_messages if item.role in {"user", "assistant"}]
        try:
            raw = await complete_json(settings, [*history, {"role": "user", "content": _context_message(request.question, sources)}])
            proposal = ProposedAnswer.model_validate_json(raw)
            claims = validate_proposal(proposal, retrieved)
            insufficient = proposal.insufficient_evidence or not claims
            if insufficient:
                claims = []
                answer = INSUFFICIENT_TEXT
                mode = "insufficient_evidence"
            else:
                answer = "\n\n".join(claim.text for claim in claims)
                mode = "llm_grounded"
        except (LLMProviderError, ValidationError, json.JSONDecodeError):
            answer = PROVIDER_ERROR_TEXT
            mode = "provider_error"

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        answer_mode=mode,
        insufficient_evidence=insufficient,
    )
    session.add(assistant_message)
    session.flush()
    if mode == "llm_grounded":
        cited_sources = {source.chunk_id: source for claim in claims for source in claim.citations}
        for source in cited_sources.values():
            session.add(Citation(
                message_id=assistant_message.id,
                chunk_id=source.chunk_id,
                document_id=source.document_id,
                filename=source.filename,
                page_number=source.page_number,
                excerpt=source.excerpt,
                citation_type="claim",
            ))
    else:
        for source in sources:
            session.add(Citation(
                message_id=assistant_message.id,
                chunk_id=source.chunk_id,
                document_id=source.document_id,
                filename=source.filename,
                page_number=source.page_number,
                excerpt=source.excerpt,
                citation_type="retrieved",
            ))
    conversation.updated_at = datetime.now(timezone.utc)
    session.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        answer=answer,
        mode=mode,
        evidence_found=bool(sources),
        insufficient_evidence=insufficient,
        claims=claims,
        sources=sources,
    )
