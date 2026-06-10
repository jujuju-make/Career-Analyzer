"""分析任务与结果模型"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Float
from app.core.database import Base


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id = Column(String(50), primary_key=True, default=lambda: f"task_{uuid.uuid4().hex[:12]}")
    resume_id = Column(String(50), nullable=False)
    target_position = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=False)
    status = Column(String(20), default="processing")  # processing | completed | failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(50), primary_key=True, default=lambda: f"result_{uuid.uuid4().hex[:12]}")
    task_id = Column(String(50), nullable=False, index=True)
    match_score = Column(Integer, nullable=True)
    strengths = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
