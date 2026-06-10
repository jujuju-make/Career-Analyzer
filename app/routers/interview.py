"""面试题生成 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import TaskRequest
from app.schemas.interview import InterviewResponse, InterviewQuestionSchema

router = APIRouter(prefix="/api/v1/interview", tags=["面试题"])


@router.post("/generate", response_model=InterviewResponse)
def generate_interview_questions(req: TaskRequest, db: Session = Depends(get_db)):
    """根据岗位要求自动生成面试题"""
    # TODO: 调用 Agent 生成面试题
    return InterviewResponse(questions=[])
