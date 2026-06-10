"""JD 分析 Agent —— 使用千问（支持文本或 PDF）"""

import os
import fitz  # PyMuPDF
from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class JDAnalyzerAgent(BaseAgent):
    """分析岗位 JD，提取关键技能和要求（使用千问）"""

    async def run(self, jd_input: str) -> dict:
        # 1. 判断输入是文本还是文件路径
        if os.path.isfile(jd_input):
            jd_text = self._extract_text(jd_input)
        else:
            jd_text = jd_input

        # 2. 调用千问分析
        llm = LLMClient("qwen")
        system_prompt = """你是一个岗位需求分析专家。请分析以下 JD，提取：
- core_skills: 核心技能要求（数组）
- bonuses: 加分项（数组）
- responsibilities: 职责描述（数组）
- experience_required: 经验年限要求
- education_required: 学历要求

以 JSON 格式返回。"""
        result = await llm.chat(system_prompt, jd_text)
        return {"raw_text": jd_text, "analysis": result}

    def _extract_text(self, file_path: str) -> str:
        """使用 PyMuPDF 提取 PDF 文本"""
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
