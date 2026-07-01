# Expert17025 — ИИ-эксперт по аккредитации лабораторий

Веб-платформа с искусственным интеллектом для консультирования испытательных лабораторий по ГОСТ ISO/IEC 17025-2019, критериям аккредитации, законодательству РФ и требованиям Росаккредитации.

## Главный принцип

**Сначала база знаний, потом ИИ.** Перед каждым обращением к языковой модели система выполняет гибридный поиск. Если готовый экспертный ответ найден (релевантность ≥ 85%), пользователь получает его без вызова LLM. Каждый новый ответ автоматически сохраняется в базу знаний.

## Архитектура

```
Пользователь → Веб-интерфейс (Next.js) → API (FastAPI)
    → Knowledge Engine (гибридный поиск)
        → если найдено → готовый ответ
        → иначе → RAG → LLM → сохранение в БЗ
```

## Стек технологий

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI, SQLAlchemy, asyncpg |
| Frontend | Next.js 15, React 19, Tailwind CSS |
| БД | PostgreSQL + pgvector |
| Кэш | Redis |
| LLM | Единый интерфейс: OpenAI, Claude, YandexGPT, GigaChat |
| RAG | Векторный поиск + парсинг PDF/DOCX/XLSX/TXT/MD/HTML |

## Модули

- **Авторизация** — регистрация, вход, JWT, роли (admin, expert, pro, free)
- **Чат** — история, Markdown, таблицы, копирование ответов
- **База знаний** — 24 категории, эмбеддинги, версионирование
- **Гибридный поиск** — семантический + ключевые слова + нормативные документы
- **RAG** — индексация документов, извлечение структуры
- **Личная база** — документы пользователя приоритетнее общей БЗ
- **Админ-панель** — аналитика, мониторинг LLM, управление БЗ
- **Самообучение** — автосохранение новых ответов

## Быстрый старт

### Docker (рекомендуется)

```bash
# Создайте .env с API-ключами
cp .env.example .env

# Запуск
docker compose up -d

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Swagger: http://localhost:8000/docs
```

### Локальная разработка

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Переключение LLM-провайдера

В `.env` или `docker-compose.yml`:

```env
LLM_PROVIDER=openai    # openai | anthropic | yandex | gigachat
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
YANDEX_API_KEY=...
YANDEX_FOLDER_ID=...
GIGACHAT_CREDENTIALS=...
```

Логика приложения не меняется — используется единый интерфейс `LLMProvider`.

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход |
| GET | `/api/chats` | Список чатов |
| POST | `/api/chats/{id}/messages` | Отправить вопрос |
| GET | `/api/knowledge/search?q=` | Поиск по БЗ |
| POST | `/api/documents/upload` | Загрузка документа |
| GET | `/api/admin/analytics` | Аналитика |

## Производительность (целевые показатели)

- Поиск по БЗ: ≤ 1 сек
- Готовый ответ: ≤ 2 сек
- Ответ ИИ: ≤ 15 сек

## Структура проекта

```
├── backend/
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── core/         # Безопасность
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── schemas/      # Pydantic схемы
│   │   └── services/
│   │       ├── knowledge_engine.py   # Гибридный поиск
│   │       ├── question_processor.py # Алгоритм обработки
│   │       └── llm/provider.py       # Абстракция LLM
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/          # Next.js pages
│       ├── components/   # UI компоненты
│       └── lib/api.ts    # API клиент
└── docker-compose.yml
```

## Следующие этапы

1. Восстановление пароля по email
2. Подписки и биллинг (PRO)
3. Объединение дубликатов в админке
4. Экспорт базы знаний
5. Полнотекстовый поиск PostgreSQL (tsvector)
6. Очередь индексации документов (Celery/Redis)
7. Наполнение начальной экспертной базы знаний
