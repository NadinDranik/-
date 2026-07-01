from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import KnowledgeCategory, KnowledgeStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeItemCreate(BaseModel):
    title: str
    category: KnowledgeCategory
    subcategory: str | None = None
    normative_document: str | None = None
    document_clause: str | None = None
    content: str
    expert_comment: str | None = None
    question_type: str | None = None
    keywords: list[str] | None = None
    related_documents: list[str] | None = None
    source: str | None = None


class KnowledgeItemUpdate(BaseModel):
    title: str | None = None
    category: KnowledgeCategory | None = None
    subcategory: str | None = None
    normative_document: str | None = None
    document_clause: str | None = None
    content: str | None = None
    expert_comment: str | None = None
    question_type: str | None = None
    keywords: list[str] | None = None
    status: KnowledgeStatus | None = None


class KnowledgeItemResponse(BaseModel):
    id: UUID
    title: str
    category: KnowledgeCategory
    subcategory: str | None
    normative_document: str | None
    document_clause: str | None
    content: str
    expert_comment: str | None
    question_type: str | None
    keywords: list[str] | None
    version: int
    status: KnowledgeStatus
    source: str | None
    usage_count: int
    rating_sum: float
    rating_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSearchResult(BaseModel):
    item: KnowledgeItemResponse
    score: float
    match_type: str


class ChatCreate(BaseModel):
    title: str | None = "Новый чат"


class ChatResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    source: str | None
    knowledge_item_id: UUID | None
    used_documents: list | None
    tokens_used: int | None
    response_time_ms: int | None
    rating: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionResponse(BaseModel):
    message: MessageResponse
    source: str
    relevance_score: float | None = None
    knowledge_item_id: UUID | None = None
    used_documents: list | None = None


class DocumentUploadResponse(BaseModel):
    id: UUID
    title: str
    filename: str
    file_type: str
    is_indexed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsSummary(BaseModel):
    total_questions: int
    total_knowledge_items: int
    llm_calls: int
    cached_answers: int
    tokens_saved: int
    average_rating: float
    popular_categories: list[dict]
