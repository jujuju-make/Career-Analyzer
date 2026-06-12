"""技能差距分析 Agent —— 使用 DeepSeek"""

import json
from app.agents.base import BaseAgent
from app.agents.llm import LLMClient


class GapAnalyzerAgent(BaseAgent):
    """对比简历技能与 JD 需求，计算匹配度 & 差距（使用 DeepSeek）"""

    async def run(self, resume_info: dict, jd_analysis: dict) -> dict:
        llm = LLMClient("deepseek")
        system_prompt = """你是该行业的技术大牛或高级工程师，有15年+ 的工作经验。你的角色是这家公司的首席技术顾问，负责最终决定是否邀请候选人面试。

你的评价标准非常高，因为你知道：
1. 这个岗位有大量竞争者，平平无奇的候选人会被迅速淘汰
2. 简历中的90%项目描述都被夸大了，实际贡献可能只有10%
3. 真正优秀的工程师会在细节中体现实力
4. 频繁跳槽、缺乏深度积累是大红旗
5. 学什么不重要，重要的是解决真实问题的能力

请对这份简历进行严苛的技术评估。你的分析应该包括（JSON 格式）：

{
  "overall_verdict": "会/不会邀请面试",
  
  "match_score": 候选人与岗位的匹配度（0-100），其中：
    - 0-30: 技能栈几乎不匹配，不建议面试
    - 31-50: 有一定基础但差距明显，很难胜任
    - 51-70: 基本满足要求但缺乏深度或某些关键技能
    - 71-85: 较好的匹配，有竞争力
    - 86-100: 几乎完美匹配，强烈推荐
  
  "critical_gaps": {
    "missing_skills": [
      {
        "skill": "具体技能名称",
        "required_proficiency": "岗位要求的熟练度",
        "candidate_proficiency": "候选人实际水平",
        "severity": "严重/中等/轻微",
        "can_be_learned": true/false,
        "why": "为什么这个差距很关键"
      }
    ],
    "experience_gaps": "具体的经验缺失（2-3句话）",
    "depth_issues": "是否存在：懂得多但都不深的问题"
  },
  
  "strengths": [
    {
      "strength": "具体优势",
      "evidence": "从简历哪里看出来的",
      "relevance_to_role": "与岗位的相关度（高/中/低）",
      "credibility": "这个优势的真实性评估（这里要很挑剔）"
    }
  ],
  
  "red_flags": [
    {
      "flag": "具体风险信号",
      "concern": "你的疑虑（直白地说）",
      "seriousness": "严重/中等/轻微"
    }
  ],
  
  "career_trajectory_analysis": "职业发展路径分析（20-50字）\n- 是否有明确的技术积累方向\n- 跳槽频率是否正常\n- 是否在深化专业度还是到处蜻蜓点水",
  
  "project_credibility": {
    "overall_assessment": "项目描述的可信度评估（高/中/低）",
    "concerns": "具体疑虑（如夸大、不合理、缺乏细节等）",
    "evidence_of_real_contribution": "是否能看出真实贡献vs虚假宣传"
  },
  
  "interview_recommendation": {
    "verdict": "是否邀请（yes/maybe/no）",
    "reason": "简洁有力的理由（1-2句）",
    "if_yes_focus_on": "如果邀请，面试重点考察什么（3-5个方向）",
    "if_no_why_waste_time": "如果不邀请，为什么觉得不合适（直白）"
  },
  
  "honest_assessment": "你最诚实的看法（100-200字）\n\n不用顾虑候选人的感受。想象你在技术社群里和朋友讨论这份简历时会说什么？这个人是不是真正的高手，还是在包装自己？和你见过的真正优秀的工程师相比，他/她在哪些方面能打动你？哪些方面让你失望？"
}

核心原则：
- 要严苛，但要有理有据
- 不要为了显得专业而无情，但也不要被表面光鲜迷惑
- 如果你会邀请面试，说出理由；如果不会，也要说清楚为什么
- 记住：大多数简历都被过度包装了，你的工作是看穿表象
"""
        user_msg = f"简历信息：{resume_info}\n\n岗位分析：{jd_analysis}"
        result = await llm.chat(system_prompt, user_msg)

        # LLM 返回的是 JSON 字符串，解析成 dict
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            parsed = {
                "match_score": None,
                "strengths": [],
                "missing_skills": [],
                "summary": result,
            }

        return {"gap_analysis": parsed}
