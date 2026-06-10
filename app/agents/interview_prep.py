"""面试题生成 Agent —— 使用 DeepSeek"""

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class InterviewPrepAgent(BaseAgent):
    """根据 JD 技能要求生成面试题（使用 DeepSeek）"""

    async def run(self, jd_analysis: dict) -> dict:
        llm = LLMClient("deepseek")
        system_prompt = """你是一个面试官。请根据岗位技能要求，生成5-8道面试题。
覆盖不同技术领域，输出 JSON 数组，每个元素包含 type（技能分类）和 question。"""
        result = await llm.chat(system_prompt, str(jd_analysis))
        return {"questions": result}
