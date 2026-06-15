"""技术一面 Agent —— 多轮对话面试"""

import json
from typing import Optional
from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class InterviewRound1Agent(BaseAgent):
    """技术一面：多轮对话面试官"""

    MODULE_CONFIG = [
        {"name": "project_experience", "label": "项目经验", "count": 6, "weight": 43},
        {"name": "job_skills", "label": "岗位技能", "count": 4, "weight": 29},
        {"name": "foundation", "label": "基础知识", "count": 3, "weight": 21},
        {"name": "behavior", "label": "行为面试", "count": 1, "weight": 7},
    ]
    TOTAL_QUESTIONS = sum(m["count"] for m in MODULE_CONFIG)  # 14

    async def generate_questions(self, resume_info: dict, jd_analysis: dict, gap_analysis: str) -> list:
        """根据简历和 JD 生成所有面试题（按模块分组）"""
        llm = LLMClient("deepseek")
        system_prompt = f"""你是一线技术面试官，负责技术一面。请根据候选人简历和 JD 生成面试题。

题目分布（共 {self.TOTAL_QUESTIONS} 题）：
1. 项目经验（6题）：深挖简历上的项目，考察真实性和技术深度
2. 岗位技能（4题）：根据 JD 要求的技术栈出题
3. 基础知识（3题）：Python、数据库、网络等通用基础
4. 行为面试（1题）：团队协作、冲突处理、职业规划

要求：
- 题目要具体，不要问八股文
- 项目题要针对简历上的具体项目来问
- 岗位技能题要针对 JD 里的技术要求
- 每道题要标注考察的能力点
- 每道题附带一个"追问"，用于候选人答得模糊时进一步考察

输出 JSON 格式（严格按照这个结构）：
{{
  "modules": [
    {{
      "name": "project_experience",
      "label": "项目经验",
      "questions": [
        {{
          "question": "具体问题",
          "expected_answer": "期望的回答要点",
          "level": "考察什么能力",
          "follow_up": "如果答得模糊，追问什么"
        }}
      ]
    }}
  ]
}}"""

        user_msg = f"""简历信息：{json.dumps(resume_info, ensure_ascii=False)}

JD 分析：{json.dumps(jd_analysis, ensure_ascii=False)}

差距分析：{gap_analysis}

请生成 {self.TOTAL_QUESTIONS} 道面试题，按模块分组。"""
        result = await llm.chat_raw(system_prompt, user_msg)

        try:
            data = json.loads(result)
            return data.get("modules", [])
        except json.JSONDecodeError:
            # 解析失败时返回默认结构
            return self._default_modules()

    async def evaluate_answer(
        self,
        question: str,
        expected_answer: str,
        follow_up: str,
        answer: str,
        history: list,
        is_follow_up: bool = False,
    ) -> dict:
        """评估候选人的回答

        Args:
            question: 原题
            expected_answer: 期望回答
            follow_up: 预设追问
            answer: 候选人的回答
            history: 之前的回答记录
            is_follow_up: 当前是否是追问

        Returns:
            { correct, score, feedback, should_follow_up }
        """
        llm = LLMClient("deepseek")

        history_text = ""
        if history:
            history_text = "之前的问答记录：\n"
            for h in history[-4:]:  # 只看最近 4 条
                history_text += f"Q: {h['question']}\nA: {h['answer']}\n评价: {h.get('feedback', '')}\n\n"

        if is_follow_up:
            system_prompt = """你是技术面试官，正在追问候选人。请评估候选人对追问的回答。

输出 JSON：
{
  "correct": "true/false/partial",
  "score": 0-100,
  "feedback": "具体的反馈，指出哪里对哪里错"
}"""
            user_msg = f"""追问：{follow_up}

候选人的回答：{answer}

{history_text}
请评估这个回答。"""
        else:
            system_prompt = """你是技术面试官，正在面试候选人。请评估候选人的回答。

评估规则：
- correct=true：回答正确完整，不追问，直接下一题
- correct=partial：回答部分正确或模糊，需要追问
- correct=false：回答错误，不追问，直接下一题

输出 JSON：
{
  "correct": "true/false/partial",
  "score": 0-100,
  "feedback": "具体的反馈，指出哪里对哪里错，以及可以补充什么"
}"""
            user_msg = f"""题目：{question}

期望回答要点：{expected_answer}

候选人的回答：{answer}

{history_text}
请评估这个回答。"""

        result = await llm.chat_raw(system_prompt, user_msg)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "correct": "partial",
                "score": 50,
                "feedback": "无法解析评估结果",
            }

    async def generate_final_verdict(self, modules: list, answers: list) -> dict:
        """所有题目答完后，生成最终 verdict"""
        llm = LLMClient("deepseek")

        # 按模块统计
        module_stats = {}
        for m in modules:
            module_stats[m["name"]] = {
                "label": m["label"],
                "weight": m["weight"],
                "questions": m["questions"],
                "answers": [a for a in answers if a["module"] == m["name"]],
            }

        system_prompt = """你是技术面试负责人，请根据候选人的面试回答记录，给出最终评价。

输出 JSON：
{
  "verdict": "pass/fail",
  "overall_score": 0-100,
  "module_scores": {
    "project_experience": 0-100,
    "job_skills": 0-100,
    "foundation": 0-100,
    "behavior": 0-100
  },
  "summary": "总体评价（50字以内）",
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "detailed_assessment": "详细评价（200字以内）"
}"""

        user_msg = f"""各模块题目和回答记录：

{json.dumps(module_stats, ensure_ascii=False, indent=2)}

请给出最终面试评价。"""
        result = await llm.chat_raw(system_prompt, user_msg)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "verdict": "fail",
                "overall_score": 0,
                "module_scores": {},
                "summary": "无法生成最终评价",
                "strengths": [],
                "weaknesses": [],
                "detailed_assessment": "",
            }

    def _default_modules(self) -> list:
        """解析失败时的默认题目"""
        return [
            {
                "name": "project_experience",
                "label": "项目经验",
                "weight": 43,
                "questions": [
                    {
                        "question": "请详细介绍一下你最近做的一个项目，包括你的角色、技术选型、遇到的挑战",
                        "expected_answer": "能清晰描述项目背景、个人贡献、技术决策",
                        "level": "项目深度",
                        "follow_up": "你提到的技术难点，具体是怎么解决的？有没有对比过其他方案？"
                    }
                ]
            }
        ]
