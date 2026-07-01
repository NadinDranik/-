from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, require_roles
from app.database import get_db
from app.models import Chat, Message, User, UserRole
from app.schemas import (
    ChatCreate,
    ChatResponse,
    MessageCreate,
    MessageResponse,
    QuestionResponse,
)
from app.services.question_processor import QuestionProcessor

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatResponse])
async def list_chats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chat).where(Chat.user_id == user.id).order_by(Chat.updated_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ChatResponse, status_code=201)
async def create_chat(
    data: ChatCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = Chat(user_id=user.id, title=data.title or "Новый чат")
    db.add(chat)
    await db.flush()
    return chat


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    chat_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = await _get_user_chat(db, chat_id, user.id)
    result = await db.execute(
        select(Message).where(Message.chat_id == chat.id).order_by(Message.created_at)
    )
    return result.scalars().all()


@router.post("/{chat_id}/messages", response_model=QuestionResponse)
async def send_message(
    chat_id: UUID,
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = await _get_user_chat(db, chat_id, user.id)

    user_msg = Message(chat_id=chat.id, role="user", content=data.content)
    db.add(user_msg)
    await db.flush()

    processor = QuestionProcessor(db)
    result = await processor.process(data.content, user_id=user.id, chat_id=chat.id)

    assistant_msg = Message(
        chat_id=chat.id,
        role="assistant",
        content=result["content"],
        source=result["source"],
        knowledge_item_id=result.get("knowledge_item_id"),
        used_documents=result.get("used_documents"),
        tokens_used=result.get("tokens_used"),
        response_time_ms=result.get("response_time_ms"),
    )
    db.add(assistant_msg)

    if chat.title == "Новый чат":
        chat.title = data.content[:80]

    await db.flush()

    return QuestionResponse(
        message=assistant_msg,
        source=result["source"],
        relevance_score=result.get("relevance_score"),
        knowledge_item_id=result.get("knowledge_item_id"),
        used_documents=result.get("used_documents"),
    )


@router.post("/{chat_id}/messages/{message_id}/rate")
async def rate_message(
    chat_id: UUID,
    message_id: UUID,
    rating: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Оценка от 1 до 5")
    await _get_user_chat(db, chat_id, user.id)
    result = await db.execute(select(Message).where(Message.id == message_id, Message.chat_id == chat_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    message.rating = rating
    if message.knowledge_item_id:
        from app.models import KnowledgeItem

        ki = await db.get(KnowledgeItem, message.knowledge_item_id)
        if ki:
            ki.rating_sum += rating
            ki.rating_count += 1
    return {"status": "ok"}


async def _get_user_chat(db: AsyncSession, chat_id: UUID, user_id: UUID) -> Chat:
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return chat
