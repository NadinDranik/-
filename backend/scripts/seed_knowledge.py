"""Скрипт начального наполнения базы знаний примерами."""

import asyncio

from app.core.embeddings import embed_text
from app.core.security import hash_password
from app.database import async_session
from app.models import KnowledgeCategory, KnowledgeItem, User, UserRole
from sqlalchemy import select


SAMPLE_ITEMS = [
    {
        "title": "Требования к внутрилабораторному контролю по п. 7.7 ГОСТ ISO/IEC 17025-2019",
        "category": KnowledgeCategory.GOST_17025,
        "normative_document": "ГОСТ ISO/IEC 17025-2019",
        "document_clause": "7.7",
        "content": """Пункт 7.7 ГОСТ ISO/IEC 17025-2019 устанавливает требования к обеспечению достоверности результатов.

Лаборатория должна иметь процедуру мониторинга достоверности результатов. Методы включают:
- использование стандартных образцов;
- повторные испытания/калибровки;
- испытания сохранённых образцов;
- корреляцию результатов разных характеристик;
- анализ полученных данных;
- внутрилабораторные сличения;
- испытания шифр-образцов.

Частота и методы ВЛК должны быть запланированы с учётом рисков и стабильности процессов.""",
        "keywords": ["влк", "7.7", "17025", "мониторинг", "достоверность"],
        "question_type": "требования",
    },
    {
        "title": "Оценка неопределённости измерений в аккредитованной лаборатории",
        "category": KnowledgeCategory.UNCERTAINTY,
        "normative_document": "ГОСТ ISO/IEC 17025-2019",
        "document_clause": "7.6",
        "content": """Пункт 7.6 требует, чтобы лаборатория определяла вклад(ы) в неопределённость измерений.

При калибровке — оценка неопределённости обязательна.
При испытаниях — когда это существенно для соответствию заявленным пределам или влияет на результат.

Неопределённость должна быть представлена в протоколе, если:
- она имеет отношение к применимости результата;
- требуется по договору, методике или заказчику.

Используются руководства GUM, EURACHEM/CITAC и отраслевые документы.""",
        "keywords": ["неопределенность", "7.6", "gum", "протокол"],
        "question_type": "метрология",
    },
    {
        "title": "Область аккредитации: основные требования",
        "category": KnowledgeCategory.SCOPE,
        "normative_document": "Приказ Минэкономразвития № 707",
        "content": """Область аккредитации должна однозначно определять компетентность лаборатории.

Включает:
- виды испытаний/измерений/отбор проб;
- объекты (продукция, материалы, среда и т.д.);
- диапазоны/характеристики;
- нормативные документы на методы (ГОСТ, МВИ, инструкции);
- сведения о СИ и вспомогательном оборудовании.

Область должна соответствовать фактическим возможностям лаборатории и подтверждаться документами СМК.""",
        "keywords": ["область аккредитации", "707", "компетентность"],
        "question_type": "аккредитация",
    },
]


async def seed():
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == "admin@expert17025.ru"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@expert17025.ru",
                hashed_password=hash_password("admin12345"),
                full_name="Администратор",
                role=UserRole.ADMIN,
                is_verified=True,
            )
            db.add(admin)
            await db.flush()

        for sample in SAMPLE_ITEMS:
            existing = await db.execute(
                select(KnowledgeItem).where(KnowledgeItem.title == sample["title"])
            )
            if existing.scalar_one_or_none():
                continue
            text_for_embed = f"{sample['title']}\n{sample['content']}"
            embedding = embed_text(text_for_embed)
            item = KnowledgeItem(**sample, embedding=embedding, source="seed")
            db.add(item)

        await db.commit()
        print("База знаний успешно наполнена примерами.")


if __name__ == "__main__":
    asyncio.run(seed())
