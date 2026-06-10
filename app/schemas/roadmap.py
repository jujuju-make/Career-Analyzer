"""学习路线 Schema"""

from pydantic import BaseModel
from typing import List


class RoadmapItemSchema(BaseModel):
    week: int
    topic: str


class RoadmapResponse(BaseModel):
    roadmap: List[RoadmapItemSchema]
