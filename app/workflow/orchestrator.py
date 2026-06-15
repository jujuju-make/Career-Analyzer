"""Agent 工作流编排 —— 使用 LangGraph 串联所有 Agent

工作流：
  ┌─────────────────────┐
  │ ResumeParser (千问)  │────┐
  └─────────────────────┘    │
                              ├──→ GapAnalyzer (DeepSeek) ──→ optimize_resume ──→ END
  ┌─────────────────────┐    │         │
  │ JDAnalyzer (千问)    │────┘         │
  └─────────────────────┘              └──→ recommend_projects ──→ END
"""

from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import operator

from langgraph.graph import StateGraph, END

from app.agents.resume_parser import ResumeParserAgent
from app.agents.jd_analyzer import JDAnalyzerAgent
from app.agents.gap_analyzer import GapAnalyzerAgent
from app.agents.resume_optimizer import ResumeOptimizationAgent
from app.agents.project_recommender import ProjectRecommenderAgent


# -------- Graph State --------

class AgentState(TypedDict):
    """工作流全局状态"""

    resume_id: str
    resume_file_path: str               # 简历 PDF 路径
    jd_input: str                       # JD 文本或文件路径
    target_position: str
    task_id: str

    # Agent 输出
    resume_parsed: dict | None          # 千问：简历解析结果
    jd_analysis: dict | None            # 千问：JD 分析结果
    gap_analysis: str | None           # DeepSeek：差距分析结果
    optimition: str | None             # DeepSeek：简历优化建议
    project_recommendations: List[Dict[str, Any]] | None  # 项目推荐结果

    # 控制
    errors: Annotated[Sequence[str], operator.add]


# -------- Node 函数 --------

async def parse_resume(state: AgentState) -> dict:
    """千问：解析简历 PDF"""
    agent = ResumeParserAgent()
    result = await agent.run(state["resume_file_path"])
    return {"resume_parsed": result}


async def analyze_jd(state: AgentState) -> dict:
    """千问：分析 JD（文本或 PDF）"""
    agent = JDAnalyzerAgent()
    result = await agent.run(state["jd_input"])
    return {"jd_analysis": result}


async def analyze_gap(state: AgentState) -> dict:
    """DeepSeek：技能差距分析"""
    agent = GapAnalyzerAgent()
    result = await agent.run(
        resume_info=state["resume_parsed"],
        jd_analysis=state["jd_analysis"],
    )
    return {"gap_analysis": result}


async def optimize_resume(state: AgentState) -> dict:
    """Deepseek: 简历优化建议（直接从 state 获取数据）"""
    agent = ResumeOptimizationAgent()
    result = await agent.run(state)
    return {"optimition": result}


async def recommend_projects(state: AgentState) -> dict:
    """根据 JD 分析结果推荐 GitHub 项目"""
    agent = ProjectRecommenderAgent()
    result = await agent.run(state["jd_analysis"])
    return {"project_recommendations": result}


# -------- 构建图 --------

def build_career_analysis_graph():
    """构建职业分析工作流图"""

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("parse_resume", parse_resume)
    workflow.add_node("analyze_jd", analyze_jd)
    workflow.add_node("analyze_gap", analyze_gap)
    workflow.add_node("optimize_resume", optimize_resume)
    workflow.add_node("recommend_projects", recommend_projects)

    """简历JD分析团队"""

    # 设置入口 —— 简历解析和 JD 分析并行启动
    workflow.set_entry_point("parse_resume")
    workflow.add_edge("__start__", "analyze_jd")

    # 简历解析和 JD 分析都完成后，进入差距分析
    workflow.add_edge("parse_resume", "analyze_gap")
    workflow.add_edge("analyze_jd", "analyze_gap")

    """能力提升团队"""

    # 差距分析完成后，简历优化和项目推荐并行执行
    workflow.add_edge("analyze_gap", "optimize_resume")
    workflow.add_edge("analyze_gap", "recommend_projects")

    # 两者都完成后结束
    workflow.add_edge("optimize_resume", END)
    workflow.add_edge("recommend_projects", END)

    return workflow.compile()
