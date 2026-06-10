"""简历模型"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text
from app.core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(50), primary_key=True, default=lambda: f"resume_{uuid.uuid4().hex[:12]}")
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(20), default="uploaded")  # uploaded | parsing | parsed | failed
    parsed_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
