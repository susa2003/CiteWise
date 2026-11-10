from pydantic import BaseModel


class PublicSettings(BaseModel):
    environment: str
    max_upload_mb: int
    llm_provider: str
    llm_configured: bool
    embedding_provider: str
    semantic_available: bool
    ocr_enabled: bool
    demo_mode: bool
