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
2. JD 需求分析（千问）- 支持文本、PDF、图片
3. 技能差距分析（DeepSeek）

返回 task_id，通过 result 接口查询分析结果。""",
    response_model=AnalysisTaskResponse,
)
async def create_analysis(req: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    import traceback
    try:
        print(f"[DEBUG] 收到请求: resume_id={req.resume_id}, target={req.target_position}, jd_type={req.jd_type}")
        print(f"[DEBUG] job_description 前100字: {str(req.job_description)[:100]}")
    except Exception as parse_err:
        print(f"[DEBUG] 参数解析失败: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"参数解析失败: {str(parse_err)}")

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
        "optimition": None,
        "project_recommendations": None,
        "errors": [],
    }

    try:
        final_state = await graph.ainvoke(initial_state)

        # 从 State 中提取各个 Agent 的输出
        gap_raw = final_state.get("gap_analysis", "") or ""

        resume_raw = final_state.get("resume_parsed", {}) or {}
        resume_data = resume_raw.get("structured", resume_raw) if isinstance(resume_raw, dict) else {}

        jd_raw = final_state.get("jd_analysis", {}) or {}
        jd_data = jd_raw.get("analysis", jd_raw) if isinstance(jd_raw, dict) else {}

        project_raw = final_state.get("project_recommendations", []) or []
        optimition_raw = final_state.get("optimition", "") or ""

        result = AnalysisResult(
            task_id=task.id,

            gap_analysis = gap_raw,
            resume_structured=resume_data,
            jd_analysis=jd_data,
            project_recommendations=project_raw,
            optimition=optimition_raw,
        )
        db.add(result)
        task.status = "completed"
        await db.commit()
    except Exception as e:
        task.status = "failed"
        await db.commit()
        import traceback
        error_detail = f"分析失败：{str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # 打印到终端
        raise HTTPException(status_code=500, detail=error_detail)

    return AnalysisTaskResponse(task_id=task.id, status="completed")


@router.get(
    "/result/{task_id}",
    summary="获取分析结果",
    description="""根据 task_id 查询完整的分析结果，包括：
1. 简历解析（HR视角）
2. JD分析（技术官视角）
3. 差距分析（技术大牛视角）—— 匹配分、优劣势、风险信号、项目可信度、面试建议、诚实评价
""",
)
async def get_analysis_result(task_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AnalysisTask).where(AnalysisTask.id == task_id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    stmt = select(AnalysisResult).where(AnalysisResult.task_id == task_id)
    result = (await db.execute(stmt)).scalar_one_or_none()

    if not result:
        return {
            "task_id": task.id,
            "target_position": task.target_position,
            "status": task.status,
            "result": None,
        }

    return result.gap_analysis
