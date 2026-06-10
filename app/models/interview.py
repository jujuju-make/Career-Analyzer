"""面试题模型"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.core.database import Base


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(String(50), primary_key=True, default=lambda: f"iq_{uuid.uuid4().hex[:12]}")
    task_id = Column(String(50), nullable=False, index=True)
    question_type = Column(String(50), nullable=False)  # e.g. Python, FastAPI
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
