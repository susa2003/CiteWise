from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.api.documents import router as documents_router
from backend.app.api.search import router as search_router
from backend.app.api.chat import router as chat_router
from backend.app.api.analysis import router as analysis_router
from backend.app.api.comparisons import router as comparisons_router
from backend.app.api.gaps import router as gaps_router
from backend.app.api.summaries import router as summaries_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.settings import router as settings_router
from backend.app.api.conversations import router as conversations_router
from backend.app.api.exports import router as exports_router
from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import get_engine
import backend.app.models  # noqa: F401 — registers ORM tables before schema initialization.


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=get_engine())
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Evidence-first research paper analysis API.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(health_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(comparisons_router, prefix="/api")
app.include_router(gaps_router, prefix="/api")
app.include_router(summaries_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(exports_router, prefix="/api")


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": settings.app_name, "status": "ready", "docs": "/docs"}
