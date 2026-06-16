"""面试 API —— 多轮对话模拟面试（按需出题）"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.database import get_db
from app.models.analysis import AnalysisTask, AnalysisResult
from app.models.interview import InterviewSession, InterviewRound
from app.agents.interview_round1 import InterviewRound1Agent

router = APIRouter(prefix="/api/v1/interview", tags=["面试"])


# -------- Schema --------

class StartInterviewRequest(BaseModel):
    """开始面试请求"""
    task_id: str = Field(..., description="分析任务 ID（来自 career/analyze）")


class QuestionData(BaseModel):
    """题目数据"""
    question: str
    question_index: int
    total: int
    module_name: str
    module_label: str
    is_follow_up: bool = False


class StartInterviewResponse(BaseModel):
    """开始面试响应"""
    session_id: str
    task_id: str
    round_name: str
    current_question: QuestionData


class AnswerRequest(BaseModel):
    """提交回答请求"""
    session_id: str = Field(..., description="面试会话 ID")
    answer: str = Field(..., description="候选人的回答")


class AnswerResult(BaseModel):
    """单题回答结果"""
    correct: str                                  # true / false / partial
    score: int
    feedback: str
    is_follow_up: bool = False                    # 当前是否是追问
    follow_up_question: Optional[str] = None      # 如果需要追问，追问内容
    next_question: Optional[QuestionData] = None  # 下一题（如果有）
    interview_over: bool = False                  # 面试是否结束
    final_result: Optional[dict] = None           # 最终结果（面试结束时）


# -------- 接口 --------

@router.post(
    "/start",
    summary="开始模拟面试",
    description="""根据分析结果开始技术一面多轮对话面试。
按需生成题目，每次只生成一道题。""",
    response_model=StartInterviewResponse,
)
async def start_interview(req: StartInterviewRequest, db: AsyncSession = Depends(get_db)):
    """开始面试，生成第一题"""
    # 查询分析结果
    stmt = select(AnalysisResult).where(AnalysisResult.task_id == req.task_id)
    result = (await db.execute(stmt)).scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=400, detail="分析结果不存在，请先完成 career/analyze")

    # 查询任务
    stmt = select(AnalysisTask).where(AnalysisTask.id == req.task_id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")

    # 生成第一题
    agent = InterviewRound1Agent()
    question_data = await agent.generate_first_question(
        resume_info=result.resume_structured or {},
        jd_analysis=result.jd_analysis or {},
        gap_analysis=result.gap_analysis or "",
    )

    if not question_data or not question_data.get("question"):
        raise HTTPException(status_code=500, detail="生成面试题失败")

    # 创建 session
    session = InterviewSession(
        task_id=req.task_id,
        round_name="tech_round1",
        status="in_progress",
        current_is_follow_up=0,
        asked_modules={"project_experience": 0, "job_skills": 0, "foundation": 0, "behavior": 0},
        current_question=question_data,
        answers=[],
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return StartInterviewResponse(
        session_id=session.id,
        task_id=req.task_id,
        round_name="tech_round1",
        current_question=QuestionData(
            question=question_data["question"],
            question_index=0,
            total=agent.TOTAL_QUESTIONS,
            module_name=question_data.get("module_name", "project_experience"),
            module_label=question_data.get("module_label", "项目经验"),
            is_follow_up=False,
        ),
    )


@router.post(
    "/answer",
    summary="提交面试回答",
    description="""提交当前题目的回答，返回评估结果和下一题（或最终结果）。

评估规则：
- correct=true → 不追问，直接下一题
- correct=partial → 追问 1 次
- correct=false → 不追问，直接下一题""",
    response_model=AnswerResult,
)
async def submit_answer(req: AnswerRequest, db: AsyncSession = Depends(get_db)):
    """提交回答，返回评估和下一题"""
    # 查询 session
    stmt = select(InterviewSession).where(InterviewSession.id == req.session_id)
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")

    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="面试已结束")

    is_follow_up = bool(session.current_is_follow_up)
    current_q = session.current_question or {}
    history = session.answers or []
    asked_modules = session.asked_modules or {}

    # 查询分析结果（用于生成下一题）
    stmt = select(AnalysisResult).where(AnalysisResult.task_id == session.task_id)
    analysis_result = (await db.execute(stmt)).scalar_one_or_none()
    stmt = select(AnalysisTask).where(AnalysisTask.id == session.task_id)
    task = (await db.execute(stmt)).scalar_one_or_none()

    # 评估回答
    agent = InterviewRound1Agent()
    evaluation = await agent.evaluate_answer(
        question=current_q.get("question", ""),
        expected_answer=current_q.get("expected_answer", ""),
        follow_up=current_q.get("follow_up", ""),
        answer=req.answer,
        history=history,
        is_follow_up=is_follow_up,
    )

    # 记录回答
    answer_record = {
        "module": current_q.get("module_name", "unknown"),
        "question": current_q.get("question", ""),
        "answer": req.answer,
        "correct": evaluation.get("correct", "partial"),
        "score": evaluation.get("score", 50),
        "feedback": evaluation.get("feedback", ""),
        "is_follow_up": is_follow_up,
    }
    all_answers = list(history) + [answer_record]
    session.answers = all_answers

    # 更新 asked_modules（原题才计数，追问不计）
    if not is_follow_up:
        module_name = current_q.get("module_name", "project_experience")
        asked_modules[module_name] = asked_modules.get(module_name, 0) + 1
        session.asked_modules = asked_modules

    correct = evaluation.get("correct", "partial")

    # 如果是原题且回答部分正确，且还有追问 → 追问
    if not is_follow_up and correct == "partial" and current_q.get("follow_up"):
        session.current_is_follow_up = 1
        await db.commit()

        # 清理追问内容中的内部说明前缀
        follow_up_text = current_q["follow_up"]
        import re
        follow_up_text = re.sub(
            r'^(如果[^，,]*[模糊不清不全][，,]\s*)?(追问[：:]?\s*)?',
            '',
            follow_up_text
        ).strip()

        return AnswerResult(
            correct=correct,
            score=evaluation.get("score", 50),
            feedback=evaluation.get("feedback", ""),
            is_follow_up=False,
            follow_up_question=follow_up_text,
            next_question=None,
            interview_over=False,
        )

    # 否则生成下一题
    next_question_data = await agent.generate_next_question(
        resume_info=analysis_result.resume_structured or {} if analysis_result else {},
        jd_analysis=analysis_result.jd_analysis or {} if analysis_result else {},
        gap_analysis=analysis_result.gap_analysis or "" if analysis_result else "",
        history=all_answers,
        asked_modules=asked_modules,
    )

    # 检查是否应该停止
    if next_question_data.get("should_stop"):
        # 所有题目答完或提前结束，生成最终结果
        final_result = await agent.generate_final_verdict(all_answers)

        session.status = "completed"
        session.verdict = final_result.get("verdict", "fail")
        session.overall_score = final_result.get("overall_score", 0)
        session.module_scores = final_result.get("module_scores", {})
        await db.commit()

        # 存盘到 InterviewRound
        interview_round = InterviewRound(
            task_id=session.task_id,
            round_name="tech_round1",
            round_order=1,
            verdict=final_result.get("verdict", "fail"),
            score=final_result.get("overall_score", 0),
            summary=final_result.get("summary", ""),
            details=final_result,
        )
        db.add(interview_round)
        await db.commit()

        return AnswerResult(
            correct=correct,
            score=evaluation.get("score", 50),
            feedback=evaluation.get("feedback", ""),
            is_follow_up=is_follow_up,
            follow_up_question=None,
            next_question=None,
            interview_over=True,
            final_result=final_result,
        )

    # 有下一题
    session.current_question = next_question_data
    session.current_is_follow_up = 0
    await db.commit()

    # 计算当前已完成的原题数
    # 注意：如果是追问回答（is_follow_up=True），asked_modules 没有增加，
    # 但实际已经完成了这轮（原题+追问），所以 question_index 应该用 total_asked
    # 如果是原题回答（is_follow_up=False），asked_modules 已经 +1，
    # total_asked 已经包含了当前这题
    total_asked = sum(asked_modules.values())
    # 如果是追问回答，total_asked 没有包含当前这轮的原题计数，
    # 但 asked_modules 在原题时已经 +1 了，所以 total_asked 是正确的
    # 前端用 currentIndex + 1 显示题号，所以这里返回的 question_index 应该是
    # 已完成的原题数（即下一题的索引，从 0 开始）
    question_index = total_asked
    total = agent.TOTAL_QUESTIONS

    return AnswerResult(
        correct=correct,
        score=evaluation.get("score", 50),
        feedback=evaluation.get("feedback", ""),
        is_follow_up=is_follow_up,
        follow_up_question=None,
        next_question=QuestionData(
            question=next_question_data["question"],
            question_index=question_index,
            total=total,
            module_name=next_question_data.get("module_name", "unknown"),
            module_label=next_question_data.get("module_label", ""),
            is_follow_up=False,
        ),
        interview_over=False,
    )


@router.get(
    "/session/{session_id}",
    summary="查询面试会话状态",
    description="""查询当前面试进度，包括已答题目、当前题目等。""",
)
async def get_session_status(session_id: str, db: AsyncSession = Depends(get_db)):
    """查询面试会话状态"""
    stmt = select(InterviewSession).where(InterviewSession.id == session_id)
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")

    asked_modules = session.asked_modules or {}
    total_asked = sum(asked_modules.values())
    agent = InterviewRound1Agent()
    current_q = session.current_question or {}

    return {
        "session_id": session.id,
        "task_id": session.task_id,
        "round_name": session.round_name,
        "status": session.status,
        "total_asked": total_asked,
        "total": agent.TOTAL_QUESTIONS,
        "current_question": current_q.get("question"),
        "current_module": current_q.get("module_label"),
        "is_follow_up": bool(session.current_is_follow_up),
        "answers_count": len(session.answers or []),
        "asked_modules": asked_modules,
        "verdict": session.verdict,
        "overall_score": session.overall_score,
        "module_scores": session.module_scores,
    }


@router.get(
    "/result/{task_id}",
    summary="查询面试结果",
    description="""查询指定分析任务的面试结果。""",
)
async def get_interview_result(task_id: str, db: AsyncSession = Depends(get_db)):
    """查询面试结果"""
    stmt = (
        select(InterviewRound)
        .where(InterviewRound.task_id == task_id)
        .order_by(InterviewRound.round_order)
    )
    rounds = (await db.execute(stmt)).scalars().all()

    if not rounds:
        raise HTTPException(status_code=404, detail="暂无面试结果")

    return {
        "task_id": task_id,
        "rounds": [
            {
                "round_name": r.round_name,
                "round_order": r.round_order,
                "verdict": r.verdict,
                "score": r.score,
                "summary": r.summary,
                "details": r.details,
            }
            for r in rounds
        ]
    }
