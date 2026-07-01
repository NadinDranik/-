import uuid
from pathlib import Path
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import get_current_user, require_roles
from app.database import get_db
from app.models import Document, DocumentScope, User, UserRole
from app.schemas import DocumentUploadResponse
from app.services.question_processor import DocumentProcessor

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()
processor = DocumentProcessor()


@router.get("", response_model=list[DocumentUploadResponse])
async def list_documents(
    scope: DocumentScope | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Document)
    if scope == DocumentScope.PERSONAL:
        stmt = stmt.where(Document.owner_id == user.id, Document.scope == DocumentScope.PERSONAL)
    elif scope == DocumentScope.GLOBAL:
        if user.role not in (UserRole.ADMIN, UserRole.EXPERT):
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        stmt = stmt.where(Document.scope == DocumentScope.GLOBAL)
    else:
        stmt = stmt.where(
            (Document.scope == DocumentScope.GLOBAL)
            | (Document.owner_id == user.id)
        )
    result = await db.execute(stmt.order_by(Document.created_at.desc()))
    return result.scalars().all()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str | None = Form(None),
    scope: DocumentScope = Form(DocumentScope.PERSONAL),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if scope == DocumentScope.GLOBAL and user.role not in (UserRole.ADMIN, UserRole.EXPERT):
        raise HTTPException(status_code=403, detail="Только администратор может загружать общие документы")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in processor.SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат. Допустимо: {', '.join(processor.SUPPORTED)}",
        )

    upload_dir = Path(settings.uploads_dir)
    if scope == DocumentScope.PERSONAL:
        upload_dir = upload_dir / "personal" / str(user.id)
    else:
        upload_dir = upload_dir / "global"
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = uuid.uuid4()
    file_path = upload_dir / f"{file_id}{suffix}"

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    document = Document(
        title=title,
        filename=file.filename or f"document{suffix}",
        file_path=str(file_path),
        file_type=suffix,
        scope=scope,
        category=category,
        owner_id=user.id if scope == DocumentScope.PERSONAL else None,
    )
    db.add(document)
    await db.flush()

    await processor.index_document(db, document)
    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")
    if doc.scope == DocumentScope.PERSONAL and doc.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    if doc.scope == DocumentScope.GLOBAL and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Нет доступа")
    await db.delete(doc)
