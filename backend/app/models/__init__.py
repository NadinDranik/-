import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EXPERT = "expert"
    PRO = "pro"
    FREE = "free"


class KnowledgeCategory(str, enum.Enum):
    GOST_17025 = "17025"
    GOST_707 = "707"
    GOST_649 = "649"
    GOST_2050 = "2050"
    FZ_412 = "412-ФЗ"
    FZ_102 = "102-ФЗ"
    SM_FSA = "СМ ФСА"
    ROSSTANDART = "Росстандарт"
    ROSACCREDITATION = "Росаккредитация"
    PK = "ПК"
    MSI = "МСИ"
    VLK = "ВЛК"
    UNCERTAINTY = "неопределенность"
    PERSONNEL = "персонал"
    EQUIPMENT = "оборудование"
    SCOPE = "область аккредитации"
    METHODS = "методики"
    CORRECTIVE = "корректирующие действия"
    RISKS = "риски"
    EXPERT_PRACTICE = "экспертная практика"
    TEMPLATES = "шаблоны"
    CASES = "реальные кейсы"
    FAQ = "FAQ"


class KnowledgeStatus(str, enum.Enum):
    ACTIVE = "active"
    OUTDATED = "outdated"
    DRAFT = "draft"
    ARCHIVED = "archived"


class DocumentScope(str, enum.Enum):
    GLOBAL = "global"
    PERSONAL = "personal"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.FREE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chats: Mapped[list["Chat"]] = relationship(back_populates="user")
    documents: Mapped[list["Document"]] = relationship(back_populates="owner")
    knowledge_items: Mapped[list["KnowledgeItem"]] = relationship(back_populates="author")


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500))
    category: Mapped[KnowledgeCategory] = mapped_column(Enum(KnowledgeCategory))
    subcategory: Mapped[str | None] = mapped_column(String(255))
    normative_document: Mapped[str | None] = mapped_column(String(500))
    document_clause: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    expert_comment: Mapped[str | None] = mapped_column(Text)
    question_type: Mapped[str | None] = mapped_column(String(100))
    keywords: Mapped[list | None] = mapped_column(JSON, default=list)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    related_documents: Mapped[list | None] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[KnowledgeStatus] = mapped_column(Enum(KnowledgeStatus), default=KnowledgeStatus.ACTIVE)
    source: Mapped[str | None] = mapped_column(String(255))
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    rating_sum: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    author_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    author: Mapped["User | None"] = relationship(back_populates="knowledge_items")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500))
    filename: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(1000))
    file_type: Mapped[str] = mapped_column(String(50))
    scope: Mapped[DocumentScope] = mapped_column(Enum(DocumentScope), default=DocumentScope.GLOBAL)
    category: Mapped[str | None] = mapped_column(String(100))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User | None"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer)
    heading: Mapped[str | None] = mapped_column(String(500))
    clause: Mapped[str | None] = mapped_column(String(255))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, default=dict)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(500), default="Новый чат")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="chats")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50))
    knowledge_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("knowledge_items.id"))
    used_documents: Mapped[list | None] = mapped_column(JSON, default=list)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped["Chat"] = relationship(back_populates="messages")


class LLMUsageLog(Base):
    __tablename__ = "llm_usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    purpose: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
