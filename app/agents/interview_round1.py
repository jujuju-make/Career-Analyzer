"""技术一面 Agent —— 按需生成面试题（动态多轮对话）"""

import json
import re
from typing import Optional
from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


def _extract_json(text: str) -> str:
    """从 LLM 返回的文本中提取 JSON 字符串（用栈匹配最外层 {}）
    
    处理 DeepSeek 返回时可能带的 ```json ... ``` 包裹、前后说明文字等。
    """
    if not text:
        return ""
    # 尝试提取 ```json ... ``` 块
    json_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_block:
        text = json_block.group(1).strip()
    start = text.find('{')
    if start == -1:
        return text.strip()
    # 用栈匹配找到最外层的 }
    stack = []
    outer_end = -1
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '{':
            stack.append(i)
        elif ch == '}':
            if stack:
                stack.pop()
                if not stack:  # 最外层闭合
                    outer_end = i
                    break
    if outer_end != -1:
        return text[start:outer_end+1]
    # 栈匹配失败，回退到 rfind
    end = text.rfind('}')
    if end > start:
        return text[start:end+1]
    return text[start:]


def _safe_json_loads(text: str) -> dict | None:
    """安全解析 JSON，自动清理 LLM 返回的文本
    
    使用 json.JSONDecoder.raw_decode 精确解析第一个完整 JSON 对象，
    避免字符串中的 {} 干扰栈匹配，也支持截断/多余文字的情况。
    """
    cleaned = _extract_json(text)
    if not cleaned:
        return None
    # 第一次尝试：正常解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # 第二次尝试：用 raw_decode 精确解析第一个完整 JSON 对象
    try:
        decoder = json.JSONDecoder()
        obj, pos = decoder.raw_decode(cleaned)
        return obj
    except json.JSONDecodeError:
        pass
    # 第三次尝试：补全缺少的 }（仅当 { 比 } 多时）
    opens = cleaned.count('{')
    closes = cleaned.count('}')
    if opens > closes:
        cleaned += '}' * (opens - closes)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
    return None


class InterviewRound1Agent(BaseAgent):
    """技术一面：按需生成面试题，根据候选人回答动态出下一题"""

    async def run(self, resume_info: dict, jd_analysis: dict, gap_analysis: str) -> dict:
        """实现 BaseAgent 抽象方法 - 兼容旧接口，生成第一题"""
        return await self.generate_first_question(resume_info, jd_analysis, gap_analysis)

    MODULE_CONFIG = [
        {"name": "project_experience", "label": "项目经验", "count": 6, "weight": 43},
        {"name": "job_skills", "label": "岗位技能", "count": 4, "weight": 29},
        {"name": "foundation", "label": "基础知识", "count": 3, "weight": 21},
        {"name": "behavior", "label": "行为面试", "count": 1, "weight": 7},
    ]
    TOTAL_QUESTIONS = sum(m["count"] for m in MODULE_CONFIG)  # 14

    async def generate_first_question(self, resume_info: dict, jd_analysis: dict, gap_analysis: str) -> dict:
        """生成第一道面试题（项目经验模块）"""
        llm = LLMClient("deepseek")
        system_prompt = f"""你是一线技术面试官，负责技术一面。请根据候选人简历和 JD 生成第一道面试题。

题目分布（共 {self.TOTAL_QUESTIONS} 题，按模块依次出题）：
1. 项目经验（6题）：深挖简历上的项目，考察真实性和技术深度
2. 岗位技能（4题）：根据 JD 要求的技术栈出题
3. 基础知识（3题）：Python、数据库、网络等通用基础
4. 行为面试（1题）：团队协作、冲突处理、职业规划

要求：
- 第一题从「项目经验」模块出
- 题目要具体，针对简历上的具体项目来问
- 不要问八股文
- question 字段只包含直接问候选人的问题，不要包含任何面试官内部说明或"如果...则追问"之类的提示
- follow_up 字段是内部使用的追问内容，不会展示给候选人

只输出 JSON，不要加任何其他文字或 Markdown 标记：
{{
  "module_name": "project_experience",
  "module_label": "项目经验",
  "question": "直接问候选人的具体问题",
  "expected_answer": "期望的回答要点",
  "level": "考察什么能力",
  "follow_up": "追问的具体问题内容（直接写问题本身，不要加"如果...则追问"等前缀）"
}}"""

        user_msg = f"""简历信息：{json.dumps(resume_info, ensure_ascii=False)}

JD 分析：{json.dumps(jd_analysis, ensure_ascii=False)}

差距分析：{gap_analysis}

请生成第一道面试题（项目经验模块）。"""
        result = await llm.chat_raw(system_prompt, user_msg)

        parsed = _safe_json_loads(result)
        if parsed and parsed.get("question"):
            return parsed

        return {
            "module_name": "project_experience",
            "module_label": "项目经验",
            "question": "请详细介绍一下你最近做的一个项目，包括你的角色、技术选型、遇到的挑战",
            "expected_answer": "能清晰描述项目背景、个人贡献、技术决策",
            "level": "项目深度",
            "follow_up": "你提到的技术难点，具体是怎么解决的？有没有对比过其他方案？"
        }

    async def generate_next_question(
        self,
        resume_info: dict,
        jd_analysis: dict,
        gap_analysis: str,
        history: list,
        asked_modules: dict,
    ) -> dict:
        """根据已答记录，动态生成下一题

        Args:
            resume_info: 简历信息
            jd_analysis: JD 分析
            gap_analysis: 差距分析
            history: 已回答记录 [{module, question, answer, correct, score}]
            asked_modules: 各模块已问题数 {"project_experience": 2, "job_skills": 0, ...}

        Returns:
            { module_name, module_label, question, expected_answer, level, follow_up }
            或 { should_stop: true, reason: "..." } 表示提前结束
        """
        llm = LLMClient("deepseek")

        # 构建已问模块统计
        module_stats = []
        for m in self.MODULE_CONFIG:
            asked = asked_modules.get(m["name"], 0)
            remaining = m["count"] - asked
            module_stats.append({
                "name": m["name"],
                "label": m["label"],
                "asked": asked,
                "total": m["count"],
                "remaining": remaining,
            })

        # 计算最近几题的平均分，判断是否提前结束
        recent_scores = [h.get("score", 50) for h in history[-3:]] if history else []
        avg_recent_score = sum(recent_scores) / len(recent_scores) if recent_scores else None

        system_prompt = f"""你是一线技术面试官，负责技术一面。请根据候选人的简历、JD 和已答记录，生成下一道面试题。

题目分布（共 {self.TOTAL_QUESTIONS} 题）：
1. 项目经验（6题）：深挖简历上的项目，考察真实性和技术深度
2. 岗位技能（4题）：根据 JD 要求的技术栈出题
3. 基础知识（3题）：Python、数据库、网络等通用基础
4. 行为面试（1题）：团队协作、冲突处理、职业规划

当前各模块进度：
{json.dumps(module_stats, ensure_ascii=False, indent=2)}

出题规则：
1. 优先出剩余题数最多的模块
2. 如果多个模块剩余相同，按顺序优先（项目经验 > 岗位技能 > 基础知识 > 行为面试）
3. 题目要具体，针对简历上的具体项目或 JD 的技术要求
4. 不要问八股文
5. question 字段只包含直接问候选人的问题，不要包含任何面试官内部说明或"如果...则追问"之类的提示
6. follow_up 字段是内部使用的追问内容，不会展示给候选人

提前结束规则：
- 如果候选人最近 3 题平均分 < 30，可以提前结束（输出 should_stop: true）
- 如果候选人最近 5 题平均分 > 85，可以提前结束（输出 should_stop: true）
- 否则正常出下一题

只输出 JSON，不要加任何其他文字或 Markdown 标记：
{{
  "should_stop": false,
  "stop_reason": null,
  "module_name": "project_experience",
  "module_label": "项目经验",
  "question": "直接问候选人的具体问题",
  "expected_answer": "期望的回答要点",
  "level": "考察什么能力",
  "follow_up": "追问的具体问题内容（直接写问题本身，不要加"如果...则追问"等前缀）"
}}

如果 should_stop 为 true，只需输出：
{{
  "should_stop": true,
  "stop_reason": "提前结束的原因"
}}"""

        user_msg = f"""简历信息：{json.dumps(resume_info, ensure_ascii=False)}

JD 分析：{json.dumps(jd_analysis, ensure_ascii=False)}

差距分析：{gap_analysis}

已回答记录（最近5条）：
{json.dumps(history[-5:], ensure_ascii=False, indent=2)}

最近平均分：{avg_recent_score}

请生成下一道面试题。"""
        result = await llm.chat_raw(system_prompt, user_msg)

        parsed = _safe_json_loads(result)
        if parsed:
            return parsed

        # 默认出下一题
        next_module = None
        for m in self.MODULE_CONFIG:
            if asked_modules.get(m["name"], 0) < m["count"]:
                next_module = m
                break

        if not next_module:
            return {"should_stop": True, "stop_reason": "所有模块题目已出完"}

        return {
            "should_stop": False,
            "module_name": next_module["name"],
            "module_label": next_module["label"],
            "question": f"请谈谈你在{next_module['label']}方面的经验（基于简历和JD要求）",
            "expected_answer": "能结合具体经历回答",
            "level": "综合能力",
            "follow_up": "能举个具体的例子吗？"
        }

    async def evaluate_answer(
        self,
        question: str,
        expected_answer: str,
        follow_up: str,
        answer: str,
        history: list,
        is_follow_up: bool = False,
    ) -> dict:
        """评估候选人的回答"""
        llm = LLMClient("deepseek")

        history_text = ""
        if history:
            history_text = "之前的问答记录：\n"
            for h in history[-4:]:
                history_text += f"Q: {h['question']}\nA: {h['answer']}\n评价: {h.get('feedback', '')}\n\n"

        if is_follow_up:
            system_prompt = """你是技术面试官，正在追问候选人。请评估候选人对追问的回答。

只输出 JSON，不要加任何其他文字或 Markdown 标记：
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

只输出 JSON，不要加任何其他文字或 Markdown 标记：
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

        parsed = _safe_json_loads(result)
        if parsed and isinstance(parsed, dict) and parsed.get("correct") in ("true", "false", "partial"):
            return parsed

        return {
            "correct": "partial",
            "score": 50,
            "feedback": "无法解析评估结果",
        }

    async def generate_final_verdict(self, history: list) -> dict:
        """所有题目答完后，生成最终 verdict"""
        llm = LLMClient("deepseek")

        # 按模块统计
        module_stats = {}
        for m in self.MODULE_CONFIG:
            module_answers = [a for a in history if a.get("module") == m["name"]]
            if module_answers:
                scores = [a.get("score", 0) for a in module_answers]
                avg_score = sum(scores) / len(scores)
            else:
                avg_score = 0
            module_stats[m["label"]] = {
                "count": len(module_answers),
                "avg_score": round(avg_score, 1),
                "answers": module_answers,
            }

        system_prompt = """你是技术面试负责人，请根据候选人的面试回答记录，给出最终评价。

只输出 JSON，不要加任何其他文字或 Markdown 标记：
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

        parsed = _safe_json_loads(result)
        if parsed and parsed.get("verdict"):
            return parsed

        return {
            "verdict": "fail",
            "overall_score": 0,
            "module_scores": {},
            "summary": "无法生成最终评价",
            "strengths": [],
            "weaknesses": [],
            "detailed_assessment": "",
        }
