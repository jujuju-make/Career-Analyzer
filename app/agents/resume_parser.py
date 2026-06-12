"""简历解析 Agent —— 使用千问"""

import fitz  # PyMuPDF
from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class ResumeParserAgent(BaseAgent):
    """解析简历 PDF，提取结构化信息（使用千问）"""

    async def run(self, file_path: str) -> dict:
        # 1. 提取 PDF 文本
        text = self._extract_text(file_path)

        # 2. 调用千问结构化（HR 视角：严格审视）
        llm = LLMClient("qwen")
        system_prompt = """你是一个资深 HR 招聘官，有10年以上招聘经验。你的工作是从大量简历中快速识别出不适配的候选人。

请以严谨、客观的 HR 视角，从以下简历中提取结构化信息。你需要：
1. 识别信息的真实性和可信度（比如夸大的表述）
2. 注意职业发展的连贯性和合理性
3. 区分核心经历和填充经历
4. 识别职位跳跃的原因（频繁跳槽？升迁？还是不得已？）

请提取以下结构化信息（JSON 格式）：
- name: 姓名
- contact: 联系方式
- education: 教育背景（学校、专业、年份）
- work_history: 工作经历列表
  - company: 公司名称
  - position: 职位
  - duration: 任职时长
  - description: 工作描述
  - red_flags: HR 角度的风险信号（如不合理跳槽、超长或超短任职等）
- core_skills: 核心技能（根据经历推断，不只是罗列）
- projects: 主要项目经验
  - name: 项目名称
  - role: 角色
  - tech_stack: 技术栈
  - outcome: 项目成果
  - credibility_score: 可信度评分（1-10，考虑是否有量化指标、是否合理等）
- professionalism_score: 专业度评分（1-10），基于排版、完整性、真实感
- overall_impression: HR 的初步印象（1-2句话，直观感受）

确保 JSON 格式完整，所有字段必须填充（没有信息时用 null）。"""
        result = await llm.chat(system_prompt, text)
        return {"raw_text": text, "structured": result}

    def _extract_text(self, file_path: str) -> str:
        """使用 PyMuPDF 提取 PDF 文本"""
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
