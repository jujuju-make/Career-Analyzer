"""面试模型"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
from app.core.database import Base


class InterviewRound(Base):
    """面试轮次结果（最终存盘）"""
    __tablename__ = "interview_rounds"

    id = Column(String(50), primary_key=True, default=lambda: f"ir_{uuid.uuid4().hex[:12]}")
    task_id = Column(String(50), nullable=False, index=True)
    round_name = Column(String(50), nullable=False)                # screen / tech_round1 / tech_round2 / leader / hr
    round_order = Column(Integer, nullable=False)

    verdict = Column(String(20), nullable=False)                   # pass / fail
    score = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)                          # 各模块得分、详细评价等

    created_at = Column(DateTime, default=datetime.utcnow)


class InterviewSession(Base):
    """面试会话状态（多轮对话进行中）"""
    __tablename__ = "interview_sessions"

    id = Column(String(50), primary_key=True, default=lambda: f"sess_{uuid.uuid4().hex[:12]}")
    task_id = Column(String(50), nullable=False, index=True)
    round_name = Column(String(50), nullable=False)                # tech_round1 / tech_round2 / leader / hr

    status = Column(String(20), default="in_progress")             # in_progress / completed / failed
    current_is_follow_up = Column(Integer, default=0)              # 当前是否是追问（0=原题, 1=追问）

    # 各模块已问题数（按需出题用）
    asked_modules = Column(JSON, default=dict)                     # {"project_experience": 0, "job_skills": 0, "foundation": 0, "behavior": 0}
    # 当前题目信息（用于恢复面试）
    current_question = Column(JSON, nullable=True)                 # {question, expected_answer, follow_up, module_name, module_label}
    # 已回答记录
    answers = Column(JSON, default=list)                           # [{module, question, answer, correct, score, feedback, is_follow_up}]

    # 最终结果
    verdict = Column(String(20), nullable=True)
    overall_score = Column(Integer, nullable=True)
    module_scores = Column(JSON, nullable=True)                    # 各模块得分

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
