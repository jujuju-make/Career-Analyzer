"""简历上传 API

上传 PDF 时自动提取文本内容，存入 parsed_content 字段
后续 Agent 直接从数据库取文本，无需再解析 PDF
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeUploadResponse

router = APIRouter(prefix="/api/v1/resume", tags=["简历"])


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传用户简历 PDF 文件，自动提取文本"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 保存文件
    file_ext = os.path.splitext(file.filename)[1] or ".pdf"
    file_id = uuid.uuid4().hex[:12]
    save_filename = f"{file_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 入库
    resume = Resume(
        filename=file.filename,
        file_path=file_path,
        status="uploaded",
    )

    # 如果是 PDF，立即提取文本
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
            resume.status = "uploaded"  # 解析失败也不影响上传

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return ResumeUploadResponse(resume_id=resume.id, status=resume.status)
