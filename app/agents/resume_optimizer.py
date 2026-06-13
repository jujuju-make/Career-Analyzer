"""优化简历Agent————deepseek"""

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient

class ResumeOptimizationAgent(BaseAgent):
    """根据简历和gap_analysis提出修改简历的建议"""

    #async def run(self, gap_data:str, resume:str):
