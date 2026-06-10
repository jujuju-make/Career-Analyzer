"""项目推荐模型"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.core.database import Base


class ProjectRecommendation(Base):
    __tablename__ = "project_recommendations"

    id = Column(String(50), primary_key=True, default=lambda: f"proj_{uuid.uuid4().hex[:12]}")
    task_id = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

