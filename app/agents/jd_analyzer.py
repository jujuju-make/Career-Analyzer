"""JD 分析 Agent —— 使用千问（支持文本或 PDF）"""
import re
import unicodedata
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

        # 2. 调用千问分析（技术面试官视角：严格把关）
        llm = LLMClient("qwen")
        system_prompt = """你是该公司的技术面试官，负责制定岗位面试标准和招聘要求。你有以下特点：
1. 你见过真正的高手，知道什么样的技能才是有竞争力的
2. 你关注候选人的实战能力，而不是简单的技能列表
3. 你能区分"看起来会"和"真的会"的差别
4. 你了解市场上该岗位的真实竞争情况——候选人池中有大量自学者和培训班出身的

请严格分析以下 JD，提取：
- core_skills: 核心技能要求（按重要程度排序）
  - skill_name: 技能名称
  - must_have: 是否必须（true/false）
  - proficiency_level: 要求的熟练度（"了解"、"熟悉"、"精通"、"10年+ 经验"）
  - why_critical: 为什么这个技能对岗位至关重要（1句话）
  - how_to_evaluate: 面试中如何考察这个技能

- nice_to_have: 加分项（数组）
  - skill_name: 技能名称
  - priority: 优先级（1-5，5最高）
  - reason: 为什么加分

- key_responsibilities: 核心职责（按优先级排序）
  - responsibility: 职责描述
  - required_skills: 这个职责需要的技能（数组）

- experience_requirement: 经验要求
  - years: 要求的工作年限
  - specific_requirements: 具体要求（如必须有什么领域的经验）
  - red_lines: 不能接受的情况（如果有的话）

- education_requirement: 学历要求
  - minimum: 最低学历
  - preferred: 优先学历
  - notes: 补充说明

- market_reality: 市场现实分析
  - difficulty_rating: 招聘难度（1-10）
  - candidate_pool_quality: 候选人池质量评估（"充足优质"、"充足但鱼龙混杂"、"紧张"）
  - realistic_salary_range: 合理薪资范围

以 JSON 格式返回。所有字段必须填充。"""
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
    

    