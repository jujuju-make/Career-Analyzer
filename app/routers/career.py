"""职业分析 API —— 一个接口触发完整工作流"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.analysis import AnalysisTask, AnalysisResult
from app.models.resume import Resume
from app.schemas.analysis import AnalysisRequest, AnalysisTaskResponse
from app.workflow.orchestrator import build_career_analysis_graph, AgentState

router = APIRouter(prefix="/api/v1/career", tags=["职业分析"])


def _safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_list(val):
    return val if isinstance(val, list) else []


def _safe_str(val):
    return str(val) if val else None


@router.post(
    "/analyze",
    summary="创建求职分析（触发完整工作流）",
    description="""根据上传的简历和目标岗位 JD，自动完成：
1. 简历解析（千问）
2. JD 需求分析（千问）
3. 技能差距分析（DeepSeek）

返回 task_id，通过 result 接口查询分析结果。""",
    response_model=AnalysisTaskResponse,
)
async def create_analysis(req: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(Resume).where(Resume.id == req.resume_id)
    resume = (await db.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    task = AnalysisTask(
        resume_id=req.resume_id,
        target_position=req.target_position,
        job_description=req.job_description,
        status="processing",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    graph = build_career_analysis_graph()
    initial_state: AgentState = {
        "resume_id": task.resume_id,
        "resume_file_path": resume.file_path,
        "jd_input": task.job_description,
        "target_position": task.target_position,
        "task_id": task.id,
        "resume_parsed": None,
        "jd_analysis": None,
        "gap_analysis": None,
        "errors": [],
    }

    try:
        final_state = await graph.ainvoke(initial_state)
        gap = final_state.get("gap_analysis", {}) or {}
        gap_data = gap.get("gap_analysis", gap) if isinstance(gap, dict) else {}

        result = AnalysisResult(
            task_id=task.id,
            match_score=_safe_int(gap_data.get("match_score")),
            strengths=_safe_list(gap_data.get("strengths")),
            missing_skills=_safe_list(gap_data.get("missing_skills")),
            summary=_safe_str(gap_data.get("summary")),
        )
        db.add(result)
        task.status = "completed"
        await db.commit()
    except Exception as e:
        task.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"分析失败：{str(e)}")

    return AnalysisTaskResponse(task_id=task.id, status="completed")


@router.get(
    "/result/{task_id}",
    summary="获取分析结果",
    description="根据 task_id 查询技能差距分析结果，包括匹配分数、优势技能、缺失技能、总结建议。",
)
async def get_analysis_result(task_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AnalysisTask).where(AnalysisTask.id == task_id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    stmt = select(AnalysisResult).where(AnalysisResult.task_id == task_id)
    result = (await db.execute(stmt)).scalar_one_or_none()

    return {
        "task_id": task.id,
        "target_position": task.target_position,
        "status": task.status,
        "result": {
            "match_score": result.match_score if result else None,
            "strengths": result.strengths if result else [],
            "missing_skills": result.missing_skills if result else [],
            "summary": result.summary if result else None,
        } if result else None,
    }
