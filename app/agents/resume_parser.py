"""简历解析 Agent —— 使用千问"""

import fitz  # PyMuPDF
from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class ResumeParserAgent(BaseAgent):
    """解析简历 PDF，提取结构化信息（使用千问）"""

    async def run(self, file_path: str) -> dict:
        # 1. 提取 PDF 文本
        text = self._extract_text(file_path)

        # 2. 调用千问结构化
        llm = LLMClient("qwen")
        system_prompt = """你是一个简历解析助手。请从以下简历文本中提取结构化信息，包括：
- name: 姓名
- contact: 联系方式
- education: 教育背景
- experience: 工作经历
- skills: 技能列表（数组）
- projects: 项目经验

以 JSON 格式返回。"""
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
