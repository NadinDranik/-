from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_roles
from app.database import get_db
from app.models import KnowledgeItem, LLMUsageLog, Message, User, UserRole
from app.schemas import AnalyticsSummary, KnowledgeItemResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics", response_model=AnalyticsSummary)
async def get_analytics(
    user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    total_questions = await db.scalar(
        select(func.count()).select_from(Message).where(Message.role == "user")
    )
    total_knowledge = await db.scalar(select(func.count()).select_from(KnowledgeItem))
    llm_calls = await db.scalar(select(func.count()).select_from(LLMUsageLog))
    cached_answers = await db.scalar(
        select(func.count()).select_from(Message).where(Message.source == "knowledge_base")
    )
    tokens_saved = await db.scalar(
        select(func.coalesce(func.sum(KnowledgeItem.usage_count * 500), 0)).select_from(KnowledgeItem)
    )
    avg_rating = await db.scalar(
        select(func.coalesce(func.avg(Message.rating), 0.0))
        .select_from(Message)
        .where(Message.rating.isnot(None))
    )

    cat_result = await db.execute(
        select(KnowledgeItem.category, func.count())
        .group_by(KnowledgeItem.category)
        .order_by(func.count().desc())
        .limit(10)
    )
    popular_categories = [{"category": str(row[0].value), "count": row[1]} for row in cat_result.all()]

    return AnalyticsSummary(
        total_questions=total_questions or 0,
        total_knowledge_items=total_knowledge or 0,
        llm_calls=llm_calls or 0,
        cached_answers=cached_answers or 0,
        tokens_saved=int(tokens_saved or 0),
        average_rating=float(avg_rating or 0),
        popular_categories=popular_categories,
    )


@router.get("/questions")
async def list_user_questions(
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Message)
        .where(Message.role == "user")
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/llm-usage")
async def llm_usage(
    user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            LLMUsageLog.provider,
            func.count(),
            func.sum(LLMUsageLog.total_tokens),
            func.sum(LLMUsageLog.estimated_cost),
        ).group_by(LLMUsageLog.provider)
    )
    return [
        {"provider": row[0], "calls": row[1], "total_tokens": row[2], "cost": row[3]}
        for row in result.all()
    ]
