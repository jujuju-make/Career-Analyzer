"""应用配置"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "AI Career Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库
    DATABASE_URL: str = "mysql+asyncmy://root:Ilikeyou1031@127.0.0.1:3306/career_analyzer"
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    CLAUDE_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    QWEN_API_KEY: Optional[str] = None

    # 文件上传
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


