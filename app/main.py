"""应用入口 —— FastAPI App"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis_client import init_redis, close_redis
from app.core.database import engine, Base
from app.routers import resume, career, interview, project


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    await init_redis()
    yield
    # 关闭时
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
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
app.include_router(interview.router)
app.include_router(project.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
