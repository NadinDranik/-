from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import admin, auth, chats, documents, knowledge
from app.config import get_settings
from app.database import Base, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from pathlib import Path

    Path("data").mkdir(exist_ok=True)
    Path(settings.uploads_dir).mkdir(exist_ok=True)

    async with engine.begin() as conn:
        if not settings.is_sqlite:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Экспертная ИИ-система по ГОСТ ISO/IEC 17025 и аккредитации испытательных лабораторий",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(chats.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "database": "sqlite" if settings.is_sqlite else "postgresql",
        "embeddings": "local" if settings.use_local_embeddings else "api",
        "llm": settings.llm_provider,
    }
