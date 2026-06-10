"""技能差距分析 Agent"""

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class GapAnalyzerAgent(BaseAgent):
    """对比简历技能与 JD 需求，计算匹配度 & 差距"""

    async def run(self, resume_info: dict, jd_analysis: dict) -> dict:
        llm = LLMClient("openai")
        system_prompt = """你是一个技能差距分析专家。请对比候选人的技能与岗位要求，输出：
- match_score (0-100 整数)
- strengths (已具备的核心优势技能列表)
- missing_skills (缺失的技能列表)
- summary (一段简短的分析总结)

以 JSON 格式返回。"""
        user_msg = f"简历信息：{resume_info}\n\n岗位分析：{jd_analysis}"
        result = await llm.chat(system_prompt, user_msg)
        return {"gap_analysis": result}
