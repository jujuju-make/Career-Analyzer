"""职业分析业务服务 —— 协调 Agent 工作流与数据库持久化

工作流：
  ① 简历+JD 联合分析
  ② 技能差距分析
  ③ 学习路线 / 面试题 / 项目推荐（并行）
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.analysis import AnalysisTask, AnalysisResult
from app.models.resume import Resume
from app.workflow.orchestrator import build_career_analysis_graph, AgentState


async def run_career_analysis(task: AnalysisTask, db: AsyncSession):
    """
    执行完整的职业分析工作流：
    1. [Agent1] 简历解析 + JD 分析（合并） — 使用上传时已提取的文本
    2. [Agent2] 技能差距分析
    3. [Agent3/4/5] 学习路线 / 面试题 / 项目推荐（并行）
    """
    # 从数据库获取简历文本（上传时已用 fitz 提取）
    stmt = select(Resume).where(Resume.id == task.resume_id)
    resume = (await db.execute(stmt)).scalar_one_or_none()
    if not resume or not resume.parsed_content:
        raise ValueError(f"简历 {task.resume_id} 不存在或尚未解析")

    graph = build_career_analysis_graph()

    initial_state: AgentState = {
        "resume_id": task.resume_id,
        "resume_text": resume.parsed_content,
        "job_description": task.job_description,
        "target_position": task.target_position,
        "task_id": task.id,
        "resume_jd_analysis": None,
        "gap_analysis": None,
        "roadmap": None,
        "interview_questions": None,
        "projects": None,
        "errors": [],
    }

    # 执行工作流
    final_state = await graph.ainvoke(initial_state)

    # 持久化分析结果（从 gap_analysis 提取）
    gap = final_state.get("gap_analysis", {}) or {}
    gap_data = gap.get("gap_analysis", gap) if isinstance(gap, dict) else {}

    result = AnalysisResult(
        task_id=task.id,
        match_score=_safe_int(gap_data.get("match_score")),
        strengths=_safe_list(gap_data.get("strengths")),
        missing_skills=_safe_list(gap_data.get("missing_skills")),
        summary=_safe_str(gap_data.get("summary")),
    )
    db.add(result)

    # 更新任务状态
    task.status = "completed"
    await db.commit()

    return final_state


def _safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_list(val):
    return val if isinstance(val, list) else []


def _safe_str(val):
    return str(val) if val else None
