from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import get_settings
from backend.app.db.session import get_engine


router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    database: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        database="ready",
    )
