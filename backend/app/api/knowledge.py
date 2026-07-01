from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_roles
from app.database import get_db
from app.models import KnowledgeItem, KnowledgeStatus, User, UserRole
from app.schemas import KnowledgeItemCreate, KnowledgeItemResponse, KnowledgeItemUpdate, KnowledgeSearchResult
from app.core.embeddings import embed_text
from app.services.knowledge_engine import KnowledgeEngine

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search", response_model=list[KnowledgeSearchResult])
async def search_knowledge(
    q: str = Query(min_length=2),
    limit: int = Query(default=10, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = KnowledgeEngine(db)
    hits = await engine.hybrid_search(q, owner_id=user.id, limit=limit)
    return [
        KnowledgeSearchResult(
            item=KnowledgeItemResponse.model_validate(hit.item),
            score=hit.score,
            match_type=hit.match_type,
        )
        for hit in hits
    ]


@router.get("", response_model=list[KnowledgeItemResponse])
async def list_knowledge(
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeItem)
        .where(KnowledgeItem.status == KnowledgeStatus.ACTIVE)
        .order_by(KnowledgeItem.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.post("", response_model=KnowledgeItemResponse, status_code=201)
async def create_knowledge(
    data: KnowledgeItemCreate,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.EXPERT)),
    db: AsyncSession = Depends(get_db),
):
    embedding = embed_text(f"{data.title}\n{data.content}")
    item = KnowledgeItem(
        **data.model_dump(),
        embedding=embedding,
        author_id=user.id,
        source="manual",
    )
    db.add(item)
    await db.flush()
    return item


@router.get("/{item_id}", response_model=KnowledgeItemResponse)
async def get_knowledge(
    item_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return item


@router.patch("/{item_id}", response_model=KnowledgeItemResponse)
async def update_knowledge(
    item_id: UUID,
    data: KnowledgeItemUpdate,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.EXPERT)),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    if data.content or data.title:
        item.embedding = embed_text(f"{item.title}\n{item.content}")
        item.version += 1
    await db.flush()
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_knowledge(
    item_id: UUID,
    user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    item.status = KnowledgeStatus.ARCHIVED
    await db.flush()
