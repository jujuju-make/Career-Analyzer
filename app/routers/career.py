"""职业分析相关 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.analysis import AnalysisTask, AnalysisResult
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisTaskResponse,
    AnalysisResultResponse,
)
from app.schemas.common import TaskRequest

router = APIRouter(prefix="/api/v1/career", tags=["职业分析"])


@router.post("/analyze", response_model=AnalysisTaskResponse)
def create_analysis(req: AnalysisRequest, db: Session = Depends(get_db)):
    """创建求职分析任务"""
    task = AnalysisTask(
        resume_id=req.resume_id,
        target_position=req.target_position,
        job_description=req.job_description,
        status="processing",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # TODO: 异步触发 Agent 分析流程

    return AnalysisTaskResponse(task_id=task.id, status="processing")


@router.get("/result/{task_id}", response_model=AnalysisResultResponse)
def get_analysis_result(task_id: str, db: Session = Depends(get_db)):
    """获取职业分析结果"""
    result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()

    if not result:
        return AnalysisResultResponse()

    return AnalysisResultResponse(
        match_score=result.match_score,
        strengths=result.strengths or [],
        missing_skills=result.missing_skills or [],
        summary=result.summary,
    )


@router.post("/roadmap")
def generate_roadmap(req: TaskRequest, db: Session = Depends(get_db)):
    """生成学习路线"""
    # TODO: 调用 Agent 生成学习路线
    return {"roadmap": []}
