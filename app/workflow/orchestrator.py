"""Agent 工作流编排 —— 使用 LangGraph 串联所有 Agent

工作流：
  [Agent1] 简历+JD 联合分析
       ↓
  [Agent2] 技能差距分析
       ↓
  ┌──────┼──────┐
  ↓      ↓      ↓
 [Agent3] [Agent4] [Agent5]
   路线    面试题    项目推荐
"""

from typing import TypedDict, Annotated, Sequence
import operator

from langgraph.graph import StateGraph, END

from app.agents.resume_jd_analyzer import ResumeJDAnalyzerAgent
from app.agents.gap_analyzer import GapAnalyzerAgent
from app.agents.roadmap_generator import RoadmapGeneratorAgent
from app.agents.interview_prep import InterviewPrepAgent
from app.agents.project_recommender import ProjectRecommenderAgent


# -------- Graph State --------

class AgentState(TypedDict):
    """工作流全局状态"""

    resume_id: str
    resume_text: str                    # 上传时已提取的简历文本
    job_description: str                # 用户输入的 JD 文本
    target_position: str
    task_id: str

    # Agent 输出
    resume_jd_analysis: dict | None   # Agent1 输出（合并）
    gap_analysis: dict | None          # Agent2 输出
    roadmap: dict | None               # Agent3 输出
    interview_questions: dict | None   # Agent4 输出
    projects: dict | None              # Agent5 输出

    # 控制
    errors: Annotated[Sequence[str], operator.add]


# -------- Node 函数 --------

async def analyze_resume_and_jd(state: AgentState) -> dict:
    """Agent1: 合并简历解析 + JD 分析"""
    agent = ResumeJDAnalyzerAgent()
    result = await agent.run(
        resume_text=state["resume_text"],
        job_description=state["job_description"],
    )
    return {"resume_jd_analysis": result}


async def analyze_gap(state: AgentState) -> dict:
    """Agent2: 技能差距分析"""
    agent = GapAnalyzerAgent()
    combined = state["resume_jd_analysis"]
    result = await agent.run(
        resume_info=combined.get("resume_structured", combined),
        jd_analysis=combined.get("jd_analysis", combined),
    )
    return {"gap_analysis": result}


async def generate_roadmap(state: AgentState) -> dict:
    """Agent3: 学习路线（依赖 gap_analysis）"""
    agent = RoadmapGeneratorAgent()
    result = await agent.run(state["gap_analysis"])
    return {"roadmap": result}


async def generate_interview_questions(state: AgentState) -> dict:
    """Agent4: 面试题（依赖 resume_jd_analysis 中的 JD 分析）"""
    agent = InterviewPrepAgent()
    jd_info = state["resume_jd_analysis"].get("jd_analysis", state["resume_jd_analysis"])
    result = await agent.run(jd_info)
    return {"interview_questions": result}


async def recommend_projects(state: AgentState) -> dict:
    """Agent5: 项目推荐（依赖 gap_analysis）"""
    agent = ProjectRecommenderAgent()
    result = await agent.run(state["gap_analysis"])
    return {"projects": result}


# -------- 构建图 --------

def build_career_analysis_graph():
    """构建职业分析工作流图"""

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("analyze_resume_and_jd", analyze_resume_and_jd)
    workflow.add_node("analyze_gap", analyze_gap)
    workflow.add_node("generate_roadmap", generate_roadmap)
    workflow.add_node("generate_interview_questions", generate_interview_questions)
    workflow.add_node("recommend_projects", recommend_projects)

    # 设置入口
    workflow.set_entry_point("analyze_resume_and_jd")

    # 串行：合并分析 → 差距分析
    workflow.add_edge("analyze_resume_and_jd", "analyze_gap")

    # 并行：差距分析后，三个下游同时执行
    workflow.add_edge("analyze_gap", "generate_roadmap")
    workflow.add_edge("analyze_gap", "generate_interview_questions")
    workflow.add_edge("analyze_gap", "recommend_projects")

    workflow.add_edge("generate_roadmap", END)
    workflow.add_edge("generate_interview_questions", END)
    workflow.add_edge("recommend_projects", END)

    return workflow.compile()
