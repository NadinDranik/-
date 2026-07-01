# Expert17025

Приватный репозиторий исходного кода. **Интерфейс приложения — не эта страница.**

## Где открыть приложение

После запуска на компьютере:

| | URL |
|---|-----|
| **Веб-интерфейс (чат)** | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

```bat
setup.bat   :: первый раз
start.bat   :: запуск backend + frontend
```

Вход по умолчанию: `admin@expert17025.ru` / `admin12345` (смените после деплоя).

## Что в репозитории

Только код. **Не коммитятся и не пушатся:**

- `backend/data/*.db` — база знаний и документы
- `backend/uploads/` — загруженные файлы
- `.env` — ключи и пароли

Подробности: [GITHUB_SETUP.md](GITHUB_SETUP.md), [docs/TECHNICAL.md](docs/TECHNICAL.md).
