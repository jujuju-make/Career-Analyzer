"""JD 分析 Agent —— 使用千问（支持文本、PDF、图片）"""
import os
from pathlib import Path
import fitz  # PyMuPDF
from app.agents.base import BaseAgent
from app.agents.llm import LLMClient

class JDAnalyzerAgent(BaseAgent):

    """分析岗位 JD，提取关键技能和要求（使用千问，支持文本/PDF/图片）"""

    async def run(self, jd_input: str) -> dict:

        """
        :param jd_input: JD 的输入，可以是：
            1. 文本内容（直接 JD 文本）
            2. 图片路径（.png, .jpg, .jpeg, .gif, .webp）
            3. PDF 路径（.pdf）
        :return: 分析结果
        """
        llm = LLMClient("qwen")
        
        # 规范化路径，避免 Windows 下路径格式问题
        normalized_path = os.path.normpath(jd_input)
        
        # 判断输入类型
        if os.path.isfile(normalized_path):
            jd_input = normalized_path

            file_path = Path(jd_input)
            suffix = file_path.suffix.lower()
            
            # 图片输入 → 使用视觉能力
            if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                return await self._analyze_jd_from_image(llm, file_path)
            # PDF 输入 → 提取文本
            elif suffix == '.pdf':
                jd_text = self._extract_text_from_pdf(file_path)
                return await self._analyze_jd_from_text(llm, jd_text)
            else:
                raise ValueError(f"不支持的文件格式: {suffix}")
        else:

            # 纯文本输入
            return await self._analyze_jd_from_text(llm, jd_input)

    async def _analyze_jd_from_image(self, llm: LLMClient, image_path: Path) -> dict:
        """从图片中解析 JD（使用千问的视觉能力）"""
        system_prompt = self._get_system_prompt()
        user_message = "请分析这份 JD 图片中的内容，提取岗位要求。"
        result = await llm.chat_with_image(system_prompt, user_message, image_path)
        return {"raw_image_path": str(image_path), "analysis": result}

    async def _analyze_jd_from_text(self, llm: LLMClient, jd_text: str) -> dict:
        """从文本中解析 JD"""
        system_prompt = self._get_system_prompt()
        result = await llm.chat(system_prompt, jd_text)
        return {"raw_text": jd_text, "analysis": result}

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是该公司的技术面试官，有8年一线开发经验，面试过300+候选人。你的工作是制定真正的面试标准——不是 JD 上写的"要求"，而是你实际面试时会淘汰人的那条线。

你很清楚：
1. JD 上写的 "熟悉 Python" 意味着候选人必须能徒手写一个 web 框架的核心逻辑，不是用过 requests 库就算
2. "了解 Docker" 意味着能写 Dockerfile 并排查容器问题，不是 run 过 nginx 镜像
3. "3年经验" 意味着至少有2个完整的商业项目周期，不是毕业到现在刚好3年
4. 市场上90%的候选人卡在"用过但不懂原理"这一关，你要定义出"什么样才算真的会"

请从技术面试官的实战视角，分析以下 JD 内容，提取真实可执行的面试标准，以JSON格式返回：

{
  "jd_title": "岗位名称",
  "company": "公司名称（如果有的话）",
  "core_skills": [
    {
      "skill_name": "技能名称",
      "must_have": true/false,
      "proficiency_level": "了解/熟悉/精通/10年+ 经验",
      "real_world_bar": "这个技能在实际工作中的真实门槛（比如'能徒手搭建一套监控体系'而不是'有监控经验'）",
      "common_pitfalls": "面试时最常见的翻车点（候选人说会但一问就倒的地方）",
      "how_to_evaluate": "面试中如何考察这个技能（具体的面试题或场景题）",
      "min_acceptable_evidence": "简历中至少要有XX经验才算过关（比如'必须有生产环境Docker使用经验'而不是'学过Docker'）"
    }
  ],
  "nice_to_have": [
    {
      "skill_name": "技能名称",
      "priority": 1-5,
      "reason": "为什么加分",
      "bonus_if": "如果候选人同时具备XX条件，加分幅度很大"
    }
  ],
  "key_responsibilities": [
    {
      "responsibility": "职责描述",
      "required_skills": ["相关技能"],
      "difficulty_level": "这个职责的难度（简单/中等/困难）",
      "typical_mistakes": "新人做这个职责常犯的错误"
    }
  ],
  "experience_requirement": {
    "years": "要求的工作年限",
    "true_requirement": "实际需要的真实能力水平（年限只是参考，比如'需要独立负责过模块设计，跟年限无关'）",
    "flexibility": "如果候选人经验稍不足但学习能力强，是否可放宽？",
    "red_lines": "绝对不能接受的情况（如'完全没做过分布式系统'、'只用过ORM没写过原生SQL'等）"
  },
  "education_requirement": {
    "minimum": "最低学历",
    "preferred": "优先学历",
    "flexibility": "什么情况下可以放宽学历要求",
    "alternative_evidence": "如果没有目标学历，可以用什么替代证明能力（如GitHub高星项目、技术博客、开源贡献等）"
  },
  "market_reality": {
    "difficulty_rating": 1-10,
    "candidate_pool_quality": "充足优质/充足但鱼龙混杂/优质稀缺/根本招不到",
    "realistic_salary_range": "合理薪资范围",
    "must_have_filter_rate": "核心硬性要求会过滤掉百分之多少的候选人（如'要求熟悉K8s可能直接刷掉70%的人'）"
  }
}

所有字段必须填充（没有信息用 null）。

注意：你的输出将直接决定后续面试官如何筛选简历。如果你标准定得太低，面试官会浪费大量时间面试不合格的人。如果你标准定得太高，可能错失有潜力的候选人。请给出经过深思熟虑的标准。"""

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """使用 PyMuPDF 提取 PDF 文本"""
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    

    
