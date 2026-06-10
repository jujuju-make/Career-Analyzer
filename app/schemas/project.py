"""项目推荐 Schema"""

from pydantic import BaseModel
from typing import List


class ProjectSchema(BaseModel):
    title: str
    reason: str


class ProjectRecommendResponse(BaseModel):
    projects: List[ProjectSchema]
