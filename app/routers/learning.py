"""学习规划 API —— 项目推荐、简历优化建议等"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.analysis import AnalysisResult

router = APIRouter(prefix="/api/v1/learning", tags=["学习规划"])


class GitHubProject(BaseModel):
    """GitHub 项目信息"""
    name: str = Field(..., description="项目全名，如 tiangolo/fastapi")
    url: str = Field(..., description="项目 GitHub 链接")
    description: str = Field("", description="项目描述")
    stars: int = Field(0, description="Star 数")
    forks: int = Field(0, description="Fork 数")
    language: Optional[str] = Field(None, description="主要编程语言")
    topics: List[str] = Field(default_factory=list, description="项目标签")


class ProjectRecommendResponse(BaseModel):
    """项目推荐响应"""
    projects: List[GitHubProject] = Field(..., description="推荐的 3 个 GitHub 项目")


class ResumeOptimizeResponse(BaseModel):
    """简历优化建议响应"""
    suggestion: str = Field(..., description="简历优化建议文本")


@router.get(
    "/recommend-projects",
    summary="获取最新分析的 GitHub 项目推荐",
    description="""获取最近一次分析结果的 GitHub 项目推荐（无需传参，自动取最新数据）。

项目推荐在 career/analyze 工作流中自动完成，与简历优化并行执行。""",
    response_model=ProjectRecommendResponse,
)
async def get_recommend_projects(db: AsyncSession = Depends(get_db)):
    """获取最新分析的 GitHub 项目推荐"""
    stmt = (
        select(AnalysisResult)
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    result = (await db.execute(stmt)).scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="暂无分析结果，请先调用 career/analyze")

    projects = result.project_recommendations
    if not projects:
        raise HTTPException(status_code=404, detail="暂无项目推荐数据")

    return ProjectRecommendResponse(projects=projects)


@router.get(
    "/resume-optimize",
    summary="获取最新分析的简历优化建议",
    description="""获取最近一次分析结果的简历优化建议（无需传参，自动取最新数据）。

简历优化在 career/analyze 工作流中自动完成，与项目推荐并行执行。""",
    response_model=ResumeOptimizeResponse,
)
async def get_resume_optimize(db: AsyncSession = Depends(get_db)):
    """获取最新分析的简历优化建议"""
    stmt = (
        select(AnalysisResult)
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    result = (await db.execute(stmt)).scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="暂无分析结果，请先调用 career/analyze")

    optimition = result.optimition
    if not optimition:
        raise HTTPException(status_code=404, detail="暂无简历优化建议数据")

    return ResumeOptimizeResponse(suggestion=optimition)
