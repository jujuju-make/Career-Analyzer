"""技能差距分析 Agent —— 使用 DeepSeek"""

import json
from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class GapAnalyzerAgent(BaseAgent):
    """对比简历技能与 JD 需求，计算匹配度 & 差距（使用 DeepSeek）"""

    async def run(self, resume_info: dict, jd_analysis: dict) -> dict:
        llm = LLMClient("deepseek")
        system_prompt = """你是一个技能差距分析专家。请对比候选人的技能与岗位要求，只输出 JSON，不要多余的文字：
{
  "match_score": 0-100的整数,
  "strengths": ["技能1", "技能2"],
  "missing_skills": ["技能3", "技能4"],
  "summary": "一段简短的分析总结"
}"""
        user_msg = f"简历信息：{resume_info}\n\n岗位分析：{jd_analysis}"
        result = await llm.chat(system_prompt, user_msg)

        # LLM 返回的是 JSON 字符串，解析成 dict
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            parsed = {
                "match_score": None,
                "strengths": [],
                "missing_skills": [],
                "summary": result,
            }

        return {"gap_analysis": parsed}
