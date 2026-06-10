"""通用 Schema"""

from pydantic import BaseModel


class TaskRequest(BaseModel):
    task_id: str
