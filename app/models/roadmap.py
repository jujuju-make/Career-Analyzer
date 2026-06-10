"""学习路线模型"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from app.core.database import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(String(50), primary_key=True, default=lambda: f"roadmap_{uuid.uuid4().hex[:12]}")
    task_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id = Column(String(50), primary_key=True, default=lambda: f"rmitem_{uuid.uuid4().hex[:12]}")
    roadmap_id = Column(String(50), ForeignKey("roadmaps.id"), nullable=False)
    week = Column(Integer, nullable=False)
    topic = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
