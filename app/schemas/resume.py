"""简历相关 Schema"""

from pydantic import BaseModel
from datetime import datetime


class ResumeUploadResponse(BaseModel):
    resume_id: str
    status: str = "success"

    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    id: str
    filename: str
    status: str
    parsed_content: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
