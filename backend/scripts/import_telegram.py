"""Импорт из папок Telegram Desktop."""
import asyncio
import os
import sys
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

from app.models import DocumentScope
from scripts.import_from_folder import import_as_documents

FOLDERS = [
    Path.home() / "Downloads" / "Telegram Desktop",
    Path.home() / "Downloads" / "Telega Desktop",
]


async def wait_for_db(max_wait: int = 3600) -> None:
    import sqlite3

    db = BACKEND_ROOT / "data" / "expert17025.db"
    for i in range(max_wait):
        try:
            c = sqlite3.connect(db, timeout=2)
            c.execute("BEGIN IMMEDIATE")
            c.rollback()
            c.close()
            return
        except sqlite3.OperationalError:
            if i % 30 == 0:
                print(f"Ожидание освобождения БД... ({i}s)")
            time.sleep(1)
    raise RuntimeError("База данных заблокирована слишком долго")


async def main():
    await wait_for_db()
    for folder in FOLDERS:
        if not folder.exists():
            print(f"[WARN] Не найдена: {folder}")
            continue
        print(f"\n{'='*50}\nИмпорт: {folder}\n{'='*50}")
        await import_as_documents(folder, DocumentScope.GLOBAL)
    print("\n[OK] Импорт Telegram завершён")


if __name__ == "__main__":
    asyncio.run(main())
