"""简历 + JD 联合分析 Agent（合并前两步）

输入：
  - resume_text: 简历纯文本（上传时已提取）
  - job_description: 用户输入的 JD 文本

输出：
  - resume_structured: 简历结构化信息（LLM 提取）
  - jd_analysis: JD 需求分析（LLM 提取）
"""

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class ResumeJDAnalyzerAgent(BaseAgent):
    """
    合并简历解析与 JD 分析
    一次 LLM 调用同时输出简历结构化和岗位需求分析
    """

    async def run(self, resume_text: str, job_description: str) -> dict:
        # 一次调用 LLM，同时分析简历 + JD
        llm = LLMClient("openai")
        system_prompt = """你是一个求职分析助手。请同时完成两项任务：

任务一：从以下简历文本中提取结构化信息（JSON格式）
- name: 姓名
- contact: 联系方式
- education: 教育背景
- experience: 工作经历
- skills: 技能列表（数组）
- projects: 项目经验

任务二：从以下 JD 中提取岗位需求（JSON格式）
- core_skills: 核心技能要求（数组）
- bonuses: 加分项（数组）
- responsibilities: 职责描述（数组）
- experience_required: 经验年限要求
- education_required: 学历要求

最终以 JSON 格式返回，包含 resume 和 jd_analysis 两个顶级字段。"""
        
        user_msg = f"【简历】\n{resume_text}\n\n【JD】\n{job_description}"
        result = await llm.chat(system_prompt, user_msg)

        return {
            "resume_structured": result,
            "jd_analysis": result,
        }
