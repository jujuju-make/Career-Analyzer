"""JD 分析 Agent"""

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class JDAnalyzerAgent(BaseAgent):
    """分析岗位 JD，提取关键技能和要求"""

    async def run(self, job_description: str) -> dict:
        llm = LLMClient("openai")
        system_prompt = """你是一个岗位需求分析专家。请分析以下 JD，提取：
- 核心技能要求
- 加分项
- 职责描述
- 经验年限要求
- 学历要求

以 JSON 格式返回。"""
        result = await llm.chat(system_prompt, job_description)
        return {"analysis": result}
