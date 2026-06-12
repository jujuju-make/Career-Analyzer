"""面试题生成 Agent —— 使用 DeepSeek"""

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class InterviewPrepAgent(BaseAgent):
    """根据 JD 技能要求生成面试题（使用 DeepSeek）"""

    async def run(self, jd_analysis: dict) -> dict:
        llm = LLMClient("deepseek")
        system_prompt = """你是一个高级面试官。根据以下JD需求和候选人的技能差距，生成8道面试题。

        题目应该分三类：
        1. 技术题（针对核心技能）
        2. 行为题（针对工作经历）  
        3. 项目题（针对缺失技能的实战应用）

        只输出 JSON 数组，格式如下：
        [
        {"type": "技术题", "skill": "Redis", "question": "..."},
        {"type": "行为题", "question": "..."},
        ...
        ]
        """
        result = await llm.chat(system_prompt, str(jd_analysis))
        return {"questions": result}
