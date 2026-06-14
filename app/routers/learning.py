"""学习规划 API —— 项目推荐、学习路线等"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.analysis import AnalysisResult, AnalysisTask
from app.agents.project_recommender import ProjectRecommenderAgent

router = APIRouter(prefix="/api/v1/learning", tags=["学习规划"])


class ProjectRecommendRequest(BaseModel):
    """项目推荐请求"""
    task_id: str = Field(..., description="分析任务 ID（来自 career/analyze 接口返回的 task_id）")


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


@router.post(
    "/recommend-projects",
    summary="推荐 GitHub 实战项目",
    description="""根据分析结果（JD 分析 + 差距分析），从 GitHub 搜索推荐 3 个 star 数最多的实战项目。

使用方式：
1. 先调用 career/analyze 获取 task_id
2. 传入 task_id，系统自动从数据库获取 JD 分析和差距分析结果
3. 返回 3 个按 stars 排序的 GitHub 项目""",
    response_model=ProjectRecommendResponse,
)
async def recommend_projects(req: ProjectRecommendRequest, db: AsyncSession = Depends(get_db)):
    """根据分析结果推荐 GitHub 项目"""
    # 查询分析结果
    stmt = select(AnalysisResult).where(AnalysisResult.task_id == req.task_id)
    result = (await db.execute(stmt)).scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在，请先调用 career/analyze")

    # 检查任务状态
    stmt = select(AnalysisTask).where(AnalysisTask.id == req.task_id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task or task.status != "completed":
        raise HTTPException(status_code=400, detail="分析任务未完成，请等待分析完成后再试")

    jd_analysis = result.jd_analysis
    if not jd_analysis:
        raise HTTPException(status_code=400, detail="JD 分析结果为空")

    try:
        agent = ProjectRecommenderAgent()
        projects = await agent.run(jd_analysis)
        return ProjectRecommendResponse(projects=projects)
    except Exception as e:
        import traceback
        error_detail = f"项目推荐失败：{str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)
