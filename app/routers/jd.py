"""JD 上传 API —— 支持文本、PDF、图片"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/api/v1/jd", tags=["岗位需求"])


class JDUploadResponse:
    """JD 上传响应（占位）"""
    pass


@router.post(
    "/upload-image",
    summary="上传 JD 图片",
    description="""上传岗位 JD 的截图或图片。支持 .png, .jpg, .jpeg, .gif, .webp 格式。
系统会使用千问的视觉能力自动解析图片中的岗位要求。""",
)
async def upload_jd_image(
    file: UploadFile = File(..., description="JD 图片文件（.png, .jpg, .jpeg, .gif, .webp）"),
    db: AsyncSession = Depends(get_db),
):
    """上传 JD 图片"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # 验证文件格式
    if file_ext not in settings.ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式。允许的格式：{', '.join(settings.ALLOWED_IMAGE_FORMATS)}"
        )
    
    # 验证文件大小
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大允许 {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.1f}MB"
        )

    # 保存文件
    file_id = uuid.uuid4().hex[:12]
    save_filename = f"jd_{file_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 统一转为绝对路径，避免路径格式问题
    abs_path = os.path.abspath(file_path)

    return {
        "jd_image_path": abs_path,
        "filename": file.filename,
        "status": "uploaded",
        "message": "JD 图片上传成功，请在分析时使用这个路径作为 job_description，并将 jd_type 设置为 image"
    }


@router.post(
    "/upload-pdf",
    summary="上传 JD PDF",
    description="""上传岗位 JD 的 PDF 文件。系统会自动提取 PDF 中的文本。""",
)
async def upload_jd_pdf(
    file: UploadFile = File(..., description="JD PDF 文件（.pdf）"),
    db: AsyncSession = Depends(get_db),
):
    """上传 JD PDF"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="只支持 PDF 格式"
        )
    
    # 验证文件大小
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大允许 {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.1f}MB"
        )

    # 保存文件
    file_id = uuid.uuid4().hex[:12]
    save_filename = f"jd_{file_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "jd_pdf_path": file_path,
        "filename": file.filename,
        "status": "uploaded",
        "message": "JD PDF 上传成功，请在分析时使用这个路径作为 job_description，并将 jd_type 设置为 pdf"
    }
