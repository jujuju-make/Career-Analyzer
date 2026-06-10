"""项目推荐 Agent"""

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class ProjectRecommenderAgent(BaseAgent):
    """根据技能缺口推荐实战项目"""

    async def run(self, gap_analysis: dict) -> dict:
        llm = LLMClient("openai")
        system_prompt = """你是一个项目推荐专家。请根据技能差距分析结果，推荐2-3个实战项目。
每个项目应能覆盖多个缺失技能。输出 JSON 数组，每个元素包含 title 和 reason。"""
        result = await llm.chat(system_prompt, str(gap_analysis))
        return {"projects": result}
