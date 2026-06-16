"""职业分析 API —— 一个接口触发完整工作流"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.analysis import AnalysisTask, AnalysisResult
from app.models.resume import Resume
from app.schemas.analysis import AnalysisRequest, AnalysisTaskResponse
from app.workflow.orchestrator import build_career_analysis_graph, AgentState

router = APIRouter(prefix="/api/v1/career", tags=["职业分析"])


def _safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_list(val):
    return val if isinstance(val, list) else []


def _safe_str(val):
    return str(val) if val else None


@router.post(
    "/analyze",
    summary="创建求职分析（触发完整工作流）",
    description="""根据上传的简历和目标岗位 JD，自动完成：
1. 简历解析（千问）
2. JD 需求分析（千问）- 支持文本、PDF、图片
3. 技能差距分析（DeepSeek）

返回 task_id，通过 result 接口查询分析结果。""",
    response_model=AnalysisTaskResponse,
)
async def create_analysis(req: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    import traceback
    try:
        print(f"[DEBUG] 收到请求: resume_id={req.resume_id}, target={req.target_position}, jd_type={req.jd_type}")
        print(f"[DEBUG] job_description 前100字: {str(req.job_description)[:100]}")
    except Exception as parse_err:
        print(f"[DEBUG] 参数解析失败: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"参数解析失败: {str(parse_err)}")

    stmt = select(Resume).where(Resume.id == req.resume_id)
    resume = (await db.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    task = AnalysisTask(
        resume_id=req.resume_id,
        target_position=req.target_position,
        job_description=req.job_description,
        status="processing",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    graph = build_career_analysis_graph()
    initial_state: AgentState = {
        "resume_id": task.resume_id,
        "resume_file_path": resume.file_path,
        "jd_input": task.job_description,
        "target_position": task.target_position,
        "task_id": task.id,
        "resume_parsed": None,
        "jd_analysis": None,
        "gap_analysis": None,
        "optimition": None,
        "project_recommendations": None,
        "errors": [],
    }

    try:
        final_state = await graph.ainvoke(initial_state)

        # 从 State 中提取各个 Agent 的输出
        gap_raw = final_state.get("gap_analysis", "") or ""

        resume_raw = final_state.get("resume_parsed", {}) or {}
        resume_data = resume_raw.get("structured", resume_raw) if isinstance(resume_raw, dict) else {}

        jd_raw = final_state.get("jd_analysis", {}) or {}
        jd_data = jd_raw.get("analysis", jd_raw) if isinstance(jd_raw, dict) else {}

        project_raw = final_state.get("project_recommendations", []) or []
        optimition_raw = final_state.get("optimition", "") or ""

        result = AnalysisResult(
            task_id=task.id,

            gap_analysis = gap_raw,
            resume_structured=resume_data,
            jd_analysis=jd_data,
            project_recommendations=project_raw,
            optimition=optimition_raw,
        )
        db.add(result)
        task.status = "completed"
        await db.commit()
    except Exception as e:
        task.status = "failed"
        await db.commit()
        import traceback
        error_detail = f"分析失败：{str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # 打印到终端
        raise HTTPException(status_code=500, detail=error_detail)

    return AnalysisTaskResponse(task_id=task.id, status="completed")


@router.get(
    "/result/{task_id}",
    summary="获取分析结果",
    description="""根据 task_id 查询完整的分析结果，包括：
1. 简历解析（HR视角）
2. JD分析（技术官视角）
3. 差距分析（技术大牛视角）—— 匹配分、优劣势、风险信号、项目可信度、面试建议、诚实评价
""",
)
async def get_analysis_result(task_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AnalysisTask).where(AnalysisTask.id == task_id)
    task = (await db.execute(stmt)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    stmt = select(AnalysisResult).where(AnalysisResult.task_id == task_id)
    result = (await db.execute(stmt)).scalar_one_or_none()

    if not result:
        return {
            "task_id": task.id,
            "target_position": task.target_position,
            "status": task.status,
            "gap_analysis": None,
            "optimition": None,
            "project_recommendations": None,
            "resume_structured": None,
            "jd_analysis": None,
        }

    # 解析 gap_analysis
    gap_analysis = result.gap_analysis
    if isinstance(gap_analysis, str):
        text = gap_analysis.strip()
        print(f"[DEBUG] gap_analysis 原始文本前100: {text[:100]}")
        # 先尝试去除 Markdown 代码块标记
        import re
        json_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_block:
            text = json_block.group(1).strip()
            print(f"[DEBUG] 去除代码块后前50: {text[:50]}")
        else:
            print(f"[DEBUG] 未匹配到代码块")
        # 用栈匹配找到最外层的 {}
        start = text.find('{')
        if start != -1:
            stack = []
            outer_end = -1
            for i in range(start, len(text)):
                if text[i] == '{':
                    stack.append(i)
                elif text[i] == '}':
                    if stack:
                        stack.pop()
                        if not stack:  # 最外层闭合
                            outer_end = i
                            break
            if outer_end != -1:
                text = text[start:outer_end+1]
                print(f"[DEBUG] 栈匹配提取后前50: {text[:50]}")
            else:
                print(f"[DEBUG] 栈匹配失败，回退到 rfind")
                end = text.rfind('}')
                if end > start:
                    text = text[start:end+1]
        try:
            parsed = json.loads(text)
            print(f"[DEBUG] JSON 解析成功，类型: {type(parsed).__name__}")
            # 新格式：{"gap_analysis": {...}} 嵌套结构
            if isinstance(parsed, dict) and "gap_analysis" in parsed:
                gap_analysis = parsed["gap_analysis"]
                print(f"[DEBUG] 嵌套格式，gap_analysis 类型: {type(gap_analysis).__name__}")
            else:
                gap_analysis = parsed
                print(f"[DEBUG] 直接格式，keys: {list(parsed.keys())[:5]}")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[DEBUG] JSON 解析失败: {e}")
            # 尝试补全缺少的 }
            if text.count('{') > text.count('}'):
                missing = text.count('{') - text.count('}')
                text_fixed = text + '}' * missing
                print(f"[DEBUG] 尝试补全 {missing} 个 }}")
                try:
                    parsed = json.loads(text_fixed)
                    print(f"[DEBUG] 补全后解析成功!")
                    if isinstance(parsed, dict) and "gap_analysis" in parsed:
                        gap_analysis = parsed["gap_analysis"]
                    else:
                        gap_analysis = parsed
                except (json.JSONDecodeError, TypeError):
                    print(f"[DEBUG] 补全后仍然解析失败")
            # 兼容旧格式：Markdown 文本 → 尝试提取关键字段
            match_score = None
            overall_verdict = None
            score_match = re.search(r'\*\*match_score\*\*\s*:\s*(\d+)', text, re.IGNORECASE)
            if score_match:
                match_score = int(score_match.group(1))
            verdict_match = re.search(r'\*\*overall_verdict\*\*\s*:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
            if verdict_match:
                overall_verdict = verdict_match.group(1).strip()
            if match_score is not None or overall_verdict is not None:
                gap_analysis = {
                    "match_score": match_score,
                    "overall_verdict": overall_verdict,
                    "verdict_reason": "",
                    "critical_gaps": {"non_negotiable_misses": [], "trainable_gaps": []},
                    "strengths": [],
                    "red_flags": [],
                    "career_trajectory_analysis": {},
                    "project_credibility": {},
                    "interview_recommendation": {"verdict": "no", "reason": ""},
                    "honest_assessment": text[:500],
                    "_raw_text": text[:2000],  # 原始 Markdown 文本，前端备用
                }
                print(f"[DEBUG] 旧格式兼容，gap_analysis 类型: {type(gap_analysis).__name__}")
            else:
                print(f"[DEBUG] 旧格式兼容也失败")

    return {
        "task_id": result.task_id,
        "target_position": task.target_position,
        "status": task.status,
        "gap_analysis": gap_analysis,
        "optimition": result.optimition,
        "project_recommendations": result.project_recommendations,
        "resume_structured": result.resume_structured,
        "jd_analysis": result.jd_analysis,
    }
