"""技能差距分析 Agent —— 使用 DeepSeek"""

import json
from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


def _extract_json(text: str) -> str:
    """从 LLM 返回的文本中提取 JSON 字符串（用栈匹配最外层 {}）"""
    import re
    if not text:
        return ""
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
    # 栈匹配失败（可能缺少 }），尝试补全
    # 先找到最后一个 } 的位置
    end = text.rfind('}')
    if end > start:
        return text[start:end+1]
    return text[start:]


class GapAnalyzerAgent(BaseAgent):
    """对比简历技能与 JD 需求，计算匹配度 & 差距，同时输出优化建议（使用 DeepSeek）"""

    async def run(self, resume_info: dict, jd_analysis: dict) -> dict:
        """返回 { gap_analysis: dict, optimition: str }"""
        llm = LLMClient("deepseek")
        system_prompt = """你是该行业的资深技术专家，带过20+人的技术团队，面试过500+候选人，亲手拒过无数名校毕业、大厂背景的候选人。你的团队每年在1000份简历里只挑10个人。

你的评估标准是基于实战经验的，你很清楚：
1. 简历上的"负责XX系统开发"大概率只是写了个CRUD接口
2. "精通"这个词在简历里99%的情况下是假的
3. 一个真正厉害的工程师，在简历的细节里就能看出来——具体的数据、合理的架构决策、踩过的坑
4. 不存在"虽然技术一般但态度好可以培养"这回事——有竞争力的岗位不缺候选人
5. 如果一个人3年经验但没有体现出任何技术深度，大概率下一个3年也不会有

现在请你对比「候选人简历信息」和「岗位JD分析结果」，直接给出你的评估

评分规则（严格遵守）：
- match_score 0-30分：技能栈严重不匹配，basic assessment failed
- match_score 31-50分：有部分基础但关键技能缺失，hiring bar达不到
- match_score 51-70分：基本满足硬性要求，但缺乏竞争力或深度存疑
- match_score 71-85分：较好的匹配，有亮点，值得认真面试
- match_score 86-100分：Strong Hire，几乎无可挑剔

注意：大多数候选人应该落在30-60分区间。如果打分超过70分，必须有充分的、可验证的证据。

请输出以下 JSON 格式（严格按照这个结构），只输出 JSON，不要加任何 Markdown 标记或说明文字：

{
  "gap_analysis": {
    "overall_verdict": "Strong Reject / Reject / Weak No / Low Priority / Maybe / Leaning Yes / Yes / Strong Yes",
    "verdict_reason": "一句话说清楚为什么是这个结论（20字以内）",
    "match_score": 0-100,
    "critical_gaps": {
      "non_negotiable_misses": ["完全缺失且短期内无法弥补的核心技能"],
      "trainable_gaps": [
        {
          "skill": "技能名称",
          "current_level": "候选人目前水平",
          "required_level": "岗位要求水平",
          "catch_up_time": "预估需要多久能追上",
          "risk_level": "高/中/低",
          "why": "为什么有这个差距以及能不能忍"
        }
      ],
      "experience_gaps": "具体的经验缺失",
      "depth_issues": "是否存在'什么都知道一点但什么都不深入'的问题？"
    },
    "strengths": [
      {
        "strength": "具体优势",
        "evidence": "从简历哪里看出来的",
        "relevance_to_role": "高/中/低",
        "credibility": "高/中/低",
        "unique_factor": "这个优势在候选人池里有多大比例的人具备？"
      }
    ],
    "red_flags": [
      {
        "flag": "具体风险信号",
        "evidence": "简历中的原文证据",
        "concern": "你的疑虑",
        "severity": "致命/严重/中等/轻微",
        "probe_question": "如果面试，你会问什么问题来验证这个风险？"
      }
    ],
    "career_trajectory_analysis": {
      "summary": "职业发展路径整体评价",
      "consistency": "一致/有变化但合理/杂乱无章",
      "growth_rate": "快速/正常/缓慢/停滞",
      "concerns": "对职业发展路径的具体疑虑"
    },
    "project_credibility": {
      "overall_assessment": "高/中/低",
      "convincing_parts": "哪些部分看起来真实可信",
      "suspicious_parts": "哪些部分听起来像夸大或编造",
      "missing_details": "缺少了什么关键信息",
      "red_herring_warning": "是否有'列了一堆技术名词但实际只是用了官方demo'的嫌疑"
    },
    "interview_recommendation": {
      "verdict": "yes/maybe/no",
      "reason": "简洁有力的理由",
      "if_yes_focus_on": ["面试必须考察的具体方向"],
      "if_no_top_reason": "拒绝的首要原因",
      "if_no_second_reason": "拒绝的次要原因",
      "alternative_suggestion": "如果有其他更适合的岗位可以推荐，没有就写 null"
    },
    "honest_assessment": "你最诚实的看法（300字以内）"
  },
  "optimition": "根据候选人的简历和gap分析，给出具体的简历修改建议。包括：1. 需要修改的地方 2. 怎么改 3. 具体示例。用中文自然语言输出，不要JSON格式。"
}"""

        user_msg = f"简历信息：{resume_info}\n\n岗位分析：{jd_analysis}"
        result = await llm.chat_raw(system_prompt, user_msg)

        # 解析 JSON，提取 gap_analysis 和 optimition
        try:
            cleaned = _extract_json(result)
            data = json.loads(cleaned)
            gap_analysis = data.get("gap_analysis", {})
            optimition = data.get("optimition", "")
        except (json.JSONDecodeError, Exception):
            gap_analysis = {"_raw_text": result[:5000]}
            # 即使 JSON 解析失败，也尝试从原始文本提取 optimition
            optimition = ""
            import re
            # 尝试匹配 "optimition": "..." 字段（处理转义）
            opt_match = re.search(r'"optimition"\s*:\s*"((?:[^"\\]|\\.)*)"', result, re.DOTALL)
            if opt_match:
                optimition = opt_match.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            else:
                # 尝试匹配 "optimition": " 到文本末尾或下一个顶层 key
                opt_match2 = re.search(r'"optimition"\s*:\s*"((?:[^"\\]|\\.)*)', result, re.DOTALL)
                if opt_match2:
                    optimition = opt_match2.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')

        return {
            "gap_analysis": json.dumps(gap_analysis, ensure_ascii=False),  # 转 JSON 字符串存入数据库
            "optimition": optimition,
        }
