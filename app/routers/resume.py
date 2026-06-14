"""简历上传 & 优化 API"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.config import settings
from app.core.database import get_db
from app.models.resume import Resume
from app.models.analysis import AnalysisTask, AnalysisResult
from app.schemas.resume import ResumeUploadResponse
from app.agents.resume_optimizer import ResumeOptimizationAgent

router = APIRouter(prefix="/api/v1/resume", tags=["简历"])


@router.post(
    "/upload",
    summary="上传简历 PDF",
    description="上传用户简历 PDF 文件，系统自动提取文本内容并保存。支持 .pdf 格式。",
    response_model=ResumeUploadResponse,
)
async def upload_resume(
    file: UploadFile = File(..., description="简历 PDF 文件（仅支持 .pdf）"),
    db: AsyncSession = Depends(get_db),
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1] or ".pdf"
    file_id = uuid.uuid4().hex[:12]
    save_filename = f"{file_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    resume = Resume(
        filename=file.filename,
        file_path=file_path,
        status="uploaded",
    )

    if file_ext.lower() == ".pdf":
        try:
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            resume.parsed_content = text.strip()
            resume.status = "parsed"
        except Exception as e:
            resume.status = "uploaded"

    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return ResumeUploadResponse(resume_id=resume.id, status=resume.status)


@router.post(
    "/optimition",
    summary="优化简历",
    description="基于最新的简历解析和差距分析结果，给出简历优化建议（无需传参，自动从数据库获取最新数据）",
)
async def optimize_resume(db: AsyncSession = Depends(get_db)):
    # 1. 获取最新的简历
    stmt = select(Resume).order_by(desc(Resume.created_at)).limit(1)
    resume = (await db.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="暂无简历数据，请先上传简历")

    # 2. 获取该简历关联的最新分析结果（含 gap_analysis）
    stmt = (
        select(AnalysisResult)
        .join(AnalysisTask, AnalysisResult.task_id == AnalysisTask.id)
        .where(AnalysisTask.resume_id == resume.id)
        .order_by(desc(AnalysisResult.created_at))
        .limit(1)
    )
    analysis_result = (await db.execute(stmt)).scalar_one_or_none()

    # 3. 拼装 state，传给 agent（从 state 里取数据）
    state = {
        "resume_parsed": resume.parsed_content or "",
        "gap_analysis": analysis_result.gap_analysis if analysis_result else "",
    }

    agent = ResumeOptimizationAgent()
    result = await agent.run(state)

    return {"resume_id": resume.id, "optimization": result}
