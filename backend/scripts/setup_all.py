"""
Полная настройка: БД + seed + импорт документов с диска.

Запуск из папки backend:
  python -m scripts.setup_all
"""

import asyncio
import os
import re
import sys
from pathlib import Path

# Корень backend в PYTHONPATH
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

from sqlalchemy import select

from app.core.embeddings import embed_text
from app.core.security import hash_password
from app.database import Base, async_session, engine
from app.models import KnowledgeCategory, KnowledgeItem, User, UserRole


def find_document_folders() -> list[Path]:
    """Ищет папки с документами на рабочем столе пользователя."""
    candidates: list[Path] = []
    home = Path.home()

    search_roots = [
        home / "OneDrive - Нефтьсервисхолдинг" / "Рабочий стол",
        home / "Desktop",
        home / "Рабочий стол",
    ]

    for root in search_roots:
        if not root.exists():
            continue
        for item in root.iterdir():
            if not item.is_dir():
                continue
            name = item.name.lower()
            if any(k in name for k in ("гост", "17025", "gost", "аккред")):
                candidates.append(item)

    # Также ищем PDF на рабочем столе
    for root in search_roots:
        if root.exists():
            for pdf in root.glob("*.pdf"):
                if "лаборатор" in pdf.stem.lower() or "17025" in pdf.stem.lower() or "аспект" in pdf.stem.lower():
                    candidates.append(pdf.parent)

    telegram_folders = [
        home / "Downloads" / "Telegram Desktop",
        home / "Downloads" / "Telega Desktop",
    ]
    for tf in telegram_folders:
        if tf.exists() and tf not in candidates:
            candidates.append(tf)

    return list(dict.fromkeys(candidates))


async def init_db():
    Path("data").mkdir(exist_ok=True)
    Path("uploads").mkdir(exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] База данных инициализирована")


async def seed_admin_and_samples():
    from scripts.seed_knowledge import SAMPLE_ITEMS

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == "admin@expert17025.ru"))
        if not result.scalar_one_or_none():
            db.add(
                User(
                    email="admin@expert17025.ru",
                    hashed_password=hash_password("admin12345"),
                    full_name="Администратор",
                    role=UserRole.ADMIN,
                    is_verified=True,
                )
            )
            await db.flush()
            print("[OK] Создан админ: admin@expert17025.ru / admin12345")

        added = 0
        for sample in SAMPLE_ITEMS:
            existing = await db.scalar(select(KnowledgeItem).where(KnowledgeItem.title == sample["title"]))
            if existing:
                continue
            text_for_embed = f"{sample['title']}\n{sample['content']}"
            item = KnowledgeItem(
                **sample,
                embedding=embed_text(text_for_embed),
                source="seed",
            )
            db.add(item)
            added += 1

        await db.commit()
        print(f"[OK] Добавлено записей seed: {added}")


async def import_blog_from_old_project():
    """Импорт статей из test17025/js/app.js"""
    blog_path = BACKEND_ROOT.parent.parent / "test17025" / "js" / "app.js"
    if not blog_path.exists():
        print("  (старый проект test17025 не найден — пропуск)")
        return

    text = blog_path.read_text(encoding="utf-8", errors="ignore")
    posts = []
    for m in re.finditer(
        r"title:\s*'([^']+)'.*?body:\s*\[(.*?)\]",
        text,
        re.DOTALL,
    ):
        title = m.group(1)
        body_parts = re.findall(r"'([^']{20,})'", m.group(2))
        if body_parts:
            posts.append({"title": title, "content": "\n\n".join(body_parts)})

    if not posts:
        return

    async with async_session() as db:
        added = 0
        for post in posts:
            existing = await db.scalar(select(KnowledgeItem).where(KnowledgeItem.title == post["title"]))
            if existing:
                continue
            db.add(
                KnowledgeItem(
                    title=post["title"],
                    category=KnowledgeCategory.FAQ,
                    content=post["content"],
                    keywords=[w for w in re.findall(r"[а-яёa-z]{4,}", post["title"].lower())][:8],
                    embedding=embed_text(f"{post['title']}\n{post['content']}"),
                    source="import:test17025",
                )
            )
            added += 1
        await db.commit()
        print(f"[OK] Импортировано статей из test17025: {added}")


async def import_documents():
    from scripts.import_from_folder import import_as_documents, import_as_knowledge

    folders = find_document_folders()
    if not folders:
        print("[WARN] Папки с документами не найдены на рабочем столе")
        return

    print(f"Найдено папок для импорта: {len(folders)}")
    for folder in folders:
        print(f"\n>> Импорт RAG из: {folder}")
        await import_as_documents(folder, scope=__import__("app.models", fromlist=["DocumentScope"]).DocumentScope.GLOBAL)

    # Для небольших docx в подпапках с номерами пунктов — knowledge mode
    for folder in folders:
        clause_folders = [f for f in folder.rglob("*") if f.is_dir() and re.match(r"^\d+\.\d+", f.name)]
        for cf in clause_folders[:5]:
            docx_count = len(list(cf.glob("*.docx")))
            if 0 < docx_count <= 30:
                print(f"\n>> Импорт БЗ из: {cf} ({docx_count} docx)")
                await import_as_knowledge(cf)


async def main():
    print("=" * 50)
    print("Expert17025 — полная настройка")
    print("=" * 50)

    await init_db()
    await seed_admin_and_samples()
    await import_blog_from_old_project()
    await import_documents()

    async with async_session() as db:
        ki_count = await db.scalar(select(__import__("sqlalchemy", fromlist=["func"]).func.count()).select_from(KnowledgeItem))
        from app.models import Document

        doc_count = await db.scalar(select(__import__("sqlalchemy", fromlist=["func"]).func.count()).select_from(Document))

    print("\n" + "=" * 50)
    print(f"Готово! Записей в БЗ: {ki_count}, документов: {doc_count}")
    print("Запуск backend: uvicorn app.main:app --reload --port 8000")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
