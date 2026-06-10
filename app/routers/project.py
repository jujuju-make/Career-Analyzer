"""项目推荐 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import TaskRequest
from app.schemas.project import ProjectRecommendResponse

router = APIRouter(prefix="/api/v1/project", tags=["项目推荐"])


@router.post("/recommend", response_model=ProjectRecommendResponse)
def recommend_projects(req: TaskRequest, db: Session = Depends(get_db)):
    """根据技能缺口推荐项目"""
    # TODO: 调用 Agent 推荐项目
    return ProjectRecommendResponse(projects=[])
