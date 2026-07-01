"""
Массовый импорт документов с локального диска в базу знаний.

Использование:
  python -m scripts.import_from_folder "C:\\путь\\к\\папке" --mode documents
  python -m scripts.import_from_folder "C:\\путь\\к\\папке" --mode knowledge

Режимы:
  documents  — загрузка файлов в RAG (таблица documents + chunks)
  knowledge  — каждый файл = одна запись в knowledge_items (для небольших текстов/docx)
"""

import argparse
import asyncio
import re
import shutil
import uuid
from pathlib import Path

from sqlalchemy import select

from app.core.embeddings import embed_text
from app.config import get_settings
from app.database import async_session
from app.models import Document, DocumentScope, KnowledgeCategory, KnowledgeItem, User, UserRole
from app.services.question_processor import DocumentProcessor

SUPPORTED = {".pdf", ".docx", ".xlsx", ".txt", ".md", ".html", ".htm"}

CATEGORY_MAP = {
    "17025": KnowledgeCategory.GOST_17025,
    "707": KnowledgeCategory.GOST_707,
    "412": KnowledgeCategory.FZ_412,
    "влк": KnowledgeCategory.VLK,
    "мси": KnowledgeCategory.MSI,
    "неопредел": KnowledgeCategory.UNCERTAINTY,
    "персонал": KnowledgeCategory.PERSONNEL,
    "оборуд": KnowledgeCategory.EQUIPMENT,
    "методик": KnowledgeCategory.METHODS,
    "коррект": KnowledgeCategory.CORRECTIVE,
    "шаблон": KnowledgeCategory.TEMPLATES,
    "кейс": KnowledgeCategory.CASES,
    "faq": KnowledgeCategory.FAQ,
}


def guess_category(path: Path) -> KnowledgeCategory:
    text = str(path).lower()
    for key, cat in CATEGORY_MAP.items():
        if key in text:
            return cat
    match = re.search(r"\\(\d+\.\d+)\\", text)
    if match:
        return KnowledgeCategory.GOST_17025
    return KnowledgeCategory.EXPERT_PRACTICE


def extract_text_simple(file_path: Path) -> str:
    processor = DocumentProcessor()
    suffix = file_path.suffix.lower()
    chunks = processor.extract_text(file_path, suffix)
    return "\n\n".join(c["content"] for c in chunks if c.get("content"))


async def import_as_documents(folder: Path, scope: DocumentScope) -> None:
    settings = get_settings()
    processor = DocumentProcessor()

    files = [f for f in folder.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED and not f.name.startswith("~$")]
    print(f"Найдено файлов: {len(files)}")

    async with async_session() as db:
        admin = await db.scalar(select(User).where(User.role == UserRole.ADMIN))
        if not admin:
            print("Ошибка: нет пользователя с ролью admin. Сначала запустите seed_knowledge.py")
            return

        imported = 0
        existing_paths = {
            (d.metadata_ or {}).get("source_path")
            for d in (await db.execute(select(Document))).scalars().all()
        }
        for file_path in files:
            source_key = str(file_path.resolve())
            if source_key in existing_paths:
                print(f"  пропуск (уже есть): {file_path.name}")
                continue

            dest_dir = Path(settings.uploads_dir) / ("global" if scope == DocumentScope.GLOBAL else "import")
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / f"{uuid.uuid4()}{file_path.suffix.lower()}"
            shutil.copy2(file_path, dest_path)

            rel = file_path.name
            if file_path.parent.name not in (folder.name, "."):
                rel = f"{file_path.parent.name} / {file_path.stem}"

            document = Document(
                title=rel[:500],
                filename=file_path.name,
                file_path=str(dest_path),
                file_type=file_path.suffix.lower(),
                scope=scope,
                category=guess_category(file_path).value,
                owner_id=None if scope == DocumentScope.GLOBAL else admin.id,
                metadata_={"source_path": source_key, "source_folder": folder.name},
            )
            db.add(document)
            await db.flush()

            try:
                count = await processor.index_document(db, document)
            except Exception as e:
                print(f"  [SKIP] {file_path.name}: {e}")
                await db.delete(document)
                continue
            imported += 1
            existing_paths.add(source_key)
            print(f"  [OK] {file_path.name} - {count} фрагментов")

        await db.commit()
        print(f"\nИмпортировано документов: {imported}")


async def import_as_knowledge(folder: Path) -> None:
    files = [f for f in folder.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED and not f.name.startswith("~$")]
    print(f"Найдено файлов: {len(files)}")

    async with async_session() as db:
        admin = await db.scalar(select(User).where(User.role == UserRole.ADMIN))
        imported = 0

        for file_path in files:
            title = file_path.stem[:500]
            existing = await db.scalar(select(KnowledgeItem).where(KnowledgeItem.title == title))
            if existing:
                print(f"  пропуск: {file_path.name}")
                continue

            try:
                content = extract_text_simple(file_path)
            except Exception as e:
                print(f"  [ERR] {file_path.name}: {e}")
                continue

            if len(content.strip()) < 50:
                print(f"  пропуск (мало текста): {file_path.name}")
                continue

            if len(content) > 15000:
                content = content[:15000] + "\n\n[... текст обрезан при импорте ...]"

            category = guess_category(file_path)
            keywords = [w for w in re.findall(r"[а-яёa-z]{4,}", title.lower())][:10]
            embedding = embed_text(f"{title}\n{content[:4000]}")

            item = KnowledgeItem(
                title=title,
                category=category,
                content=content,
                keywords=keywords,
                embedding=embedding,
                author_id=admin.id if admin else None,
                source=f"import:{file_path.name}",
            )
            db.add(item)
            imported += 1
            print(f"  [OK] {file_path.name}")

        await db.commit()
        print(f"\nИмпортировано записей: {imported}")


def main():
    parser = argparse.ArgumentParser(description="Импорт файлов с диска в Expert17025")
    parser.add_argument("folder", help="Путь к папке с документами")
    parser.add_argument(
        "--mode",
        choices=["documents", "knowledge"],
        default="documents",
        help="documents = RAG, knowledge = готовые записи БЗ",
    )
    parser.add_argument(
        "--scope",
        choices=["global", "personal"],
        default="global",
        help="Область видимости (только для mode=documents)",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"Папка не найдена: {folder}")
        return

    scope = DocumentScope.GLOBAL if args.scope == "global" else DocumentScope.PERSONAL

    if args.mode == "documents":
        asyncio.run(import_as_documents(folder, scope))
    else:
        asyncio.run(import_as_knowledge(folder))


if __name__ == "__main__":
    main()
