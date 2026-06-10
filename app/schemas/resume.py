"""简历相关 Schema"""

from pydantic import BaseModel, Field
from datetime import datetime


class ResumeUploadResponse(BaseModel):
    resume_id: str = Field(..., description="简历唯一标识，如 resume_xxx")
    status: str = Field("success", description="上传状态：uploaded（仅保存）/ parsed（已提取文本）")
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

