"""分析任务与结果 Schema"""

from pydantic import BaseModel
from datetime import datetime
from typing import List


class AnalysisRequest(BaseModel):
    resume_id: str
    target_position: str
    job_description: str


class AnalysisTaskResponse(BaseModel):
    task_id: str
    status: str = "processing"


class AnalysisResultResponse(BaseModel):
    match_score: int | None = None
    strengths: List[str] = []
    missing_skills: List[str] = []
    summary: str | None = None
