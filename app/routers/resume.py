"""简历上传 API"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeUploadResponse

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
