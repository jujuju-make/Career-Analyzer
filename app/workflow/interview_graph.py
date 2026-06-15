"""面试工作流编排 —— 使用 LangGraph 串联面试流程

工作流：
  screen_resume（基于 gap_analyzer 结果筛选）
    ↓ 条件边：yes/maybe → tech_round1；no → END
  tech_round1（技术一面）
    ↓ 条件边：pass → tech_round2；fail → END
  tech_round2（技术二面）
    ↓ 条件边：pass → leader_round；fail → END
  leader_round（Leader 面）
    ↓ 条件边：pass → hr_round；fail → END
  hr_round（HR 面）
    ↓
  END
"""

from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Literal
import operator
import json

from langgraph.graph import StateGraph, END

from app.agents.gap_analyzer import GapAnalyzerAgent
from app.agents.interview_round1 import InterviewRound1Agent


# -------- Graph State --------

class InterviewState(TypedDict):
    """面试工作流全局状态"""

    task_id: str                        # 关联 analysis_tasks
    resume_id: str
    target_position: str

    # 来自 career 分析的结果
    resume_parsed: dict | None
    jd_analysis: dict | None
    gap_analysis: str | None

    # 各轮面试结果
    screen_result: dict | None          # 筛选结果（复用 gap_analyzer 的 interview_recommendation）
    round1_result: dict | None          # 技术一面结果
    round2_result: dict | None          # 技术二面结果
    leader_result: dict | None          # Leader 面结果
    hr_result: dict | None              # HR 面结果

    # 控制
    errors: Annotated[Sequence[str], operator.add]


# -------- 条件判断函数 --------

def should_proceed_to_round1(state: InterviewState) -> Literal["tech_round1", "fail"]:
    """根据筛选结果决定是否进入技术一面"""
    screen = state.get("screen_result", {}) or {}
    verdict = screen.get("verdict", "no")
    if verdict in ("yes", "maybe"):
        return "tech_round1"
    return "fail"


def should_proceed_to_round2(state: InterviewState) -> Literal["tech_round2", "fail"]:
    """根据技术一面结果决定是否进入二面"""
    r1 = state.get("round1_result", {}) or {}
    verdict = r1.get("verdict", "fail")
    if verdict == "pass":
        return "tech_round2"
    return "fail"


def should_proceed_to_leader(state: InterviewState) -> Literal["leader_round", "fail"]:
    """根据技术二面结果决定是否进入 Leader 面"""
    r2 = state.get("round2_result", {}) or {}
    verdict = r2.get("verdict", "fail")
    if verdict == "pass":
        return "leader_round"
    return "fail"


def should_proceed_to_hr(state: InterviewState) -> Literal["hr_round", "fail"]:
    """根据 Leader 面结果决定是否进入 HR 面"""
    ld = state.get("leader_result", {}) or {}
    verdict = ld.get("verdict", "fail")
    if verdict == "pass":
        return "hr_round"
    return "fail"


# -------- Node 函数 --------

async def screen_resume(state: InterviewState) -> dict:
    """基于 gap_analyzer 结果做筛选决策"""
    gap_raw = state.get("gap_analysis", "")
    if not gap_raw:
        return {
            "screen_result": {
                "verdict": "no",
                "score": 0,
                "summary": "无差距分析数据",
            }
        }

    # 从 gap_analysis JSON 中提取 interview_recommendation
    try:
        gap_data = json.loads(gap_raw) if isinstance(gap_raw, str) else gap_raw
        interview_rec = gap_data.get("interview_recommendation", {})
        verdict = interview_rec.get("verdict", "no")
        score = gap_data.get("match_score", 0)
        reason = interview_rec.get("reason", "")
        return {
            "screen_result": {
                "verdict": verdict,
                "score": score,
                "summary": reason,
                "details": gap_data,
            }
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "screen_result": {
                "verdict": "maybe",
                "score": 50,
                "summary": "无法解析 gap_analysis，默认进入面试",
            }
        }


async def tech_round1(state: InterviewState) -> dict:
    """技术一面：coding + 基础知识"""
    agent = InterviewRound1Agent()
    result = await agent.run(
        resume_info=state.get("resume_parsed", {}),
        jd_analysis=state.get("jd_analysis", {}),
        gap_analysis=state.get("gap_analysis", ""),
    )
    return {"round1_result": result}


async def tech_round2(state: InterviewState) -> dict:
    """技术二面：深度 + 系统设计（预留）"""
    # TODO: 实现技术二面 Agent
    return {
        "round2_result": {
            "verdict": "pass",
            "score": 70,
            "summary": "技术二面（预留）",
        }
    }


async def leader_round(state: InterviewState) -> dict:
    """Leader 面：综合评估（预留）"""
    # TODO: 实现 Leader 面 Agent
    return {
        "leader_result": {
            "verdict": "pass",
            "score": 70,
            "summary": "Leader 面（预留）",
        }
    }


async def hr_round(state: InterviewState) -> dict:
    """HR 面：薪资、入职意向（预留）"""
    # TODO: 实现 HR 面 Agent
    return {
        "hr_result": {
            "verdict": "pass",
            "score": 70,
            "summary": "HR 面（预留）",
        }
    }


async def fail_end(state: InterviewState) -> dict:
    """面试终止节点"""
    return {}


# -------- 构建图 --------

def build_interview_graph():
    """构建面试工作流图"""

    workflow = StateGraph(InterviewState)

    # 添加节点
    workflow.add_node("screen_resume", screen_resume)
    workflow.add_node("tech_round1", tech_round1)
    workflow.add_node("tech_round2", tech_round2)
    workflow.add_node("leader_round", leader_round)
    workflow.add_node("hr_round", hr_round)
    workflow.add_node("fail", fail_end)

    # 设置入口
    workflow.set_entry_point("screen_resume")

    # 条件边
    workflow.add_conditional_edges(
        "screen_resume",
        should_proceed_to_round1,
        {
            "tech_round1": "tech_round1",
            "fail": "fail",
        }
    )

    workflow.add_conditional_edges(
        "tech_round1",
        should_proceed_to_round2,
        {
            "tech_round2": "tech_round2",
            "fail": "fail",
        }
    )

    workflow.add_conditional_edges(
        "tech_round2",
        should_proceed_to_leader,
        {
            "leader_round": "leader_round",
            "fail": "fail",
        }
    )

    workflow.add_conditional_edges(
        "leader_round",
        should_proceed_to_hr,
        {
            "hr_round": "hr_round",
            "fail": "fail",
        }
    )

    # 终节点
    workflow.add_edge("hr_round", END)
    workflow.add_edge("fail", END)

    return workflow.compile()
