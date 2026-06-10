"""学习路线生成 Agent —— 使用 DeepSeek"""

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class RoadmapGeneratorAgent(BaseAgent):
    """根据技能差距生成个性化学习路线（使用 DeepSeek）"""

    async def run(self, gap_analysis: dict) -> dict:
        llm = LLMClient("deepseek")
        system_prompt = """你是一个学习规划师。请根据技能差距分析结果，制定一个4-6周的学习路线。
每周一个主题，从基础到进阶排列。

以 JSON 数组格式返回，每个元素包含 week 和 topic。"""
        result = await llm.chat(system_prompt, str(gap_analysis))
        return {"roadmap": result}
