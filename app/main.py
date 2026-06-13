"""应用入口 —— FastAPI App"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis_client import init_redis, close_redis
from app.core.database import init_db
from app.routers import resume, career, interview, project, jd


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    await init_db()       # 自动建表
    await init_redis()
    yield
    # 关闭时
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    description="""AI Career Agent 是一个面向求职者的智能职业规划系统。

## 使用流程
1. **上传简历** → `POST /api/v1/resume/upload`（上传 PDF，自动解析文本）
2. **发起分析** → `POST /api/v1/career/analyze`（传入 resume_id + 目标岗位 + JD 文本，触发完整工作流）
3. **查看结果** → `GET /api/v1/career/result/{task_id}`（查询技能差距分析结果）

## Agent 工作流
- 简历解析 → **千问**
- JD 分析 → **千问**
- 技能差距分析 → **DeepSeek**
""",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(resume.router)
app.include_router(career.router)
app.include_router(jd.router)
app.include_router(interview.router)
app.include_router(project.router)
@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

