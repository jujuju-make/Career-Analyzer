"""Agent 基类"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """所有 Agent 的抽象基类"""

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name

    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        """执行 Agent 的核心逻辑"""
        pass
