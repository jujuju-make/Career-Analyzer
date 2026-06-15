"""面试 API —— 多轮对话模拟面试"""

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


# -------- 辅助函数 --------

def _get_current_question(modules: list, q_idx: int) -> tuple:
    """根据 question_index 找到对应的题目和模块"""
    idx = 0
    for m in modules:
        for q in m.get("questions", []):
            if idx == q_idx:
                return m, q
            idx += 1
    return None, None


def _get_total_questions(modules: list) -> int:
    """计算总题数"""
    return sum(len(m.get("questions", [])) for m in modules)


# -------- 接口 --------

@router.post(
    "/start",
    summary="开始模拟面试",
    description="""根据分析结果开始技术一面多轮对话面试。

生成 14 道题（项目经验6题 + 岗位技能4题 + 基础知识3题 + 行为面试1题），返回第一题。""",
    response_model=StartInterviewResponse,
)
async def start_interview(req: StartInterviewRequest, db: AsyncSession = Depends(get_db)):
    """开始面试，生成题目，返回第一题"""
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

    # 生成题目
    agent = InterviewRound1Agent()
    modules = await agent.generate_questions(
        resume_info=result.resume_structured or {},
        jd_analysis=result.jd_analysis or {},
        gap_analysis=result.gap_analysis or "",
    )

    if not modules or not modules[0].get("questions"):
        raise HTTPException(status_code=500, detail="生成面试题失败")

    # 创建 session
    session = InterviewSession(
        task_id=req.task_id,
        round_name="tech_round1",
        status="in_progress",
        current_question_index=0,
        current_is_follow_up=0,
        modules=modules,
        answers=[],
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # 返回第一题
    total = _get_total_questions(modules)
    m, q = _get_current_question(modules, 0)

    return StartInterviewResponse(
        session_id=session.id,
        task_id=req.task_id,
        round_name="tech_round1",
        current_question=QuestionData(
            question=q["question"],
            question_index=0,
            total=total,
            module_name=m["name"],
            module_label=m["label"],
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

    modules = session.modules
    q_idx = session.current_question_index
    is_follow_up = session.current_is_follow_up
    total = _get_total_questions(modules)

    # 找到当前题目
    m, q = _get_current_question(modules, q_idx)
    if not q:
        raise HTTPException(status_code=500, detail="题目数据异常")

    # 评估回答
    agent = InterviewRound1Agent()
    history = session.answers or []

    evaluation = await agent.evaluate_answer(
        question=q["question"],
        expected_answer=q.get("expected_answer", ""),
        follow_up=q.get("follow_up", ""),
        answer=req.answer,
        history=history,
        is_follow_up=bool(is_follow_up),
    )

    # 记录回答
    answer_record = {
        "q_idx": q_idx,
        "module": m["name"],
        "question": q["question"],
        "answer": req.answer,
        "correct": evaluation.get("correct", "partial"),
        "score": evaluation.get("score", 50),
        "feedback": evaluation.get("feedback", ""),
        "is_follow_up": bool(is_follow_up),
    }
    all_answers = list(history) + [answer_record]
    session.answers = all_answers

    # 决定下一步
    correct = evaluation.get("correct", "partial")

    # 如果是原题且回答部分正确，且还有追问没用 → 追问
    if not is_follow_up and correct == "partial" and q.get("follow_up"):
        session.current_is_follow_up = 1
        await db.commit()

        return AnswerResult(
            correct=correct,
            score=evaluation.get("score", 50),
            feedback=evaluation.get("feedback", ""),
            is_follow_up=False,
            follow_up_question=q["follow_up"],
            next_question=None,
            interview_over=False,
        )

    # 否则进入下一题
    next_q_idx = q_idx + 1

    # 如果还有下一题
    if next_q_idx < total:
        session.current_question_index = next_q_idx
        session.current_is_follow_up = 0
        await db.commit()

        next_m, next_q = _get_current_question(modules, next_q_idx)

        return AnswerResult(
            correct=correct,
            score=evaluation.get("score", 50),
            feedback=evaluation.get("feedback", ""),
            is_follow_up=bool(is_follow_up),
            follow_up_question=None,
            next_question=QuestionData(
                question=next_q["question"],
                question_index=next_q_idx,
                total=total,
                module_name=next_m["name"],
                module_label=next_m["label"],
                is_follow_up=False,
            ),
            interview_over=False,
        )

    # 所有题目答完，生成最终结果
    final_result = await agent.generate_final_verdict(modules, all_answers)

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
        is_follow_up=bool(is_follow_up),
        follow_up_question=None,
        next_question=None,
        interview_over=True,
        final_result=final_result,
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

    modules = session.modules
    total = _get_total_questions(modules)
    m, q = _get_current_question(modules, session.current_question_index)

    return {
        "session_id": session.id,
        "task_id": session.task_id,
        "round_name": session.round_name,
        "status": session.status,
        "current_question_index": session.current_question_index,
        "total": total,
        "current_question": q["question"] if q else None,
        "current_module": m["label"] if m else None,
        "is_follow_up": bool(session.current_is_follow_up),
        "answers_count": len(session.answers or []),
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
