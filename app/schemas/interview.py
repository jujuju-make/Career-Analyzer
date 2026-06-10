"""面试题 Schema"""

from pydantic import BaseModel
from typing import List


class InterviewQuestionSchema(BaseModel):
    type: str
    question: str


class InterviewResponse(BaseModel):
    questions: List[InterviewQuestionSchema]
