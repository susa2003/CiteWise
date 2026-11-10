from typing import Literal

from pydantic import BaseModel


class ExportRequest(BaseModel):
    run_id: str
    format: Literal["pdf", "docx"]
