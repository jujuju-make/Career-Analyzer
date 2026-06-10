"""分析任务与结果 Schema"""

from pydantic import BaseModel, Field
from typing import List, Optional


class AnalysisRequest(BaseModel):
    resume_id: str = Field(..., description="上传简历时返回的 resume_id，如 resume_xxx")
    target_position: str = Field(..., description="目标岗位名称，如 AI Agent开发实习生")
    job_description: str = Field(..., description="岗位描述文本（支持直接粘贴 JD 全文）")
class AnalysisTaskResponse(BaseModel):
    task_id: str = Field(..., description="分析任务 ID，用于查询结果，如 task_xxx")
    status: str = Field("processing", description="任务状态：processing / completed / failed")
class AnalysisResultData(BaseModel):
    match_score: Optional[int] = Field(None, description="技能匹配度评分（0-100）")
    strengths: List[str] = Field(default_factory=list, description="已具备的优势技能")
    missing_skills: List[str] = Field(default_factory=list, description="缺失的技能")
    summary: Optional[str] = Field(None, description="综合分析总结与建议")
class AnalysisFullResponse(BaseModel):
    task_id: str = Field(..., description="分析任务 ID")
    target_position: str = Field(..., description="目标岗位")
    status: str = Field(..., description="任务状态")
    result: Optional[AnalysisResultData] = Field(None, description="分析结果数据")

