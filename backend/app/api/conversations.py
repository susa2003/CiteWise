from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.session import get_db
from backend.app.models.conversation import Conversation, Message
from backend.app.schemas.chat import ConversationListItem, ConversationRead, StoredCitation, StoredMessage


router = APIRouter(prefix="/conversations", tags=["chat"])


@router.get("", response_model=list[ConversationListItem])
def list_conversations(session: Session = Depends(get_db)) -> list[ConversationListItem]:
    items = session.scalars(select(Conversation).order_by(Conversation.updated_at.desc()).limit(50)).all()
    return [ConversationListItem(id=item.id, title=item.title, created_at=item.created_at.isoformat(), updated_at=item.updated_at.isoformat()) for item in items]


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(conversation_id: str, session: Session = Depends(get_db)) -> ConversationRead:
    conversation = session.scalar(
        select(Conversation)
        .options(selectinload(Conversation.messages).selectinload(Message.citations))
        .where(Conversation.id == conversation_id)
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return ConversationRead(
        id=conversation.id,
        title=conversation.title,
        messages=[StoredMessage(
            id=message.id,
            role=message.role,
            content=message.content,
            answer_mode=message.answer_mode,
            insufficient_evidence=message.insufficient_evidence,
            created_at=message.created_at.isoformat(),
            citations=[StoredCitation(
                chunk_id=citation.chunk_id,
                document_id=citation.document_id,
                filename=citation.filename,
                page_number=citation.page_number,
                excerpt=citation.excerpt,
                citation_type=citation.citation_type,
            ) for citation in message.citations],
        ) for message in conversation.messages],
    )
