from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.schemas.settings import PublicSettings


router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=PublicSettings)
def read_public_settings() -> PublicSettings:
    settings = get_settings()
    semantic_ready = False
    if settings.embedding_provider == "sentence_transformers":
        try:
            import chromadb  # noqa: F401
            import sentence_transformers  # noqa: F401
            semantic_ready = True
        except ImportError:
            semantic_ready = False
    return PublicSettings(
        environment=settings.environment,
        max_upload_mb=settings.max_upload_mb,
        llm_provider=settings.llm_provider,
        llm_configured=settings.llm_is_configured,
        embedding_provider=settings.embedding_provider,
        semantic_available=semantic_ready,
        ocr_enabled=settings.ocr_enabled,
        demo_mode=not settings.llm_is_configured,
    )
