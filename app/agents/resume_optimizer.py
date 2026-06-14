"""优化简历Agent————deepseek"""

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient

class ResumeOptimizationAgent(BaseAgent):
    """根据简历和gap_analysis提出修改简历的建议"""

    async def run(self, state: dict) -> str:
        """从 state 中直接获取简历解析结果和 gap 分析结果"""
        llm = LLMClient("deepseek")
        system_prompt = """ 你是一个有10年经验的职业规划与分析师，你对各行各业的情形了如指掌，明白它们的需求，
        你需要明确点明简历中哪里需要改，怎么改，并为候选人推荐项目。以下是回答样例：
        
        “根据候选人的简历和gap分析，我认为这些地方需要修改：
        1. ......
        2. ......
        .......（其他需要改动的地方）”
        
        """

        resume = state.get("resume_parsed", "")
        gap_data = state.get("gap_analysis", "")
        user_msg = f"简历信息{resume}\n\n gap分析{gap_data}"
        result = await llm.chat_raw(system_prompt, user_msg)

        return result
