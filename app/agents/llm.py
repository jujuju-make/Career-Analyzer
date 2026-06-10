"""LLM 客户端封装（支持 OpenAI / DeepSeek / 千问）"""

from typing import Optional
from openai import AsyncOpenAI

from app.core.config import settings


# 各厂商的模型名常量
MODEL_QWEN = "qwen-plus"           # 千问
MODEL_DEEPSEEK = "deepseek-chat"   # DeepSeek


class LLMClient:
    """统一的 LLM 调用客户端"""

    def __init__(self, provider: str = "deepseek"):
        self.provider = provider
        self.client = self._build_client()

    def _build_client(self) -> AsyncOpenAI:
        api_key_map = {
            "deepseek": settings.DEEPSEEK_API_KEY,
            "qwen": settings.QWEN_API_KEY,
        }
        base_url_map = {
            "deepseek": "https://api.deepseek.com/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }

        api_key = api_key_map.get(self.provider)
        base_url = base_url_map.get(self.provider)

        if not api_key:
            raise ValueError(f"未配置 {self.provider} 的 API Key")

        return AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(self, system_prompt: str, user_message: str, **kwargs) -> str:
        """调用 LLM 进行对话"""
        # 不同 provider 默认模型不同
        default_model = kwargs.pop("model", None)
        if not default_model:
            model_map = {
                "deepseek": "deepseek-chat",
                "qwen": "qwen-plus",
            }
            default_model = model_map.get(self.provider, "deepseek-chat")

        response = await self.client.chat.completions.create(
            model=default_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            **kwargs,
        )
        return response.choices[0].message.content
