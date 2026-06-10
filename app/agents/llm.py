"""LLM 客户端封装（支持 OpenAI / Claude / DeepSeek）"""

from typing import Optional
from openai import AsyncOpenAI

from app.core.config import settings


class LLMClient:
    """统一的 LLM 调用客户端"""

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.client = self._build_client()

    def _build_client(self) -> AsyncOpenAI:
        api_key_map = {
            "openai": settings.OPENAI_API_KEY,
            "deepseek": settings.DEEPSEEK_API_KEY,
        }
        base_url_map = {
            "openai": "https://api.openai.com/v1",
            "deepseek": "https://api.deepseek.com/v1",
        }

        api_key = api_key_map.get(self.provider)
        base_url = base_url_map.get(self.provider)

        if not api_key:
            raise ValueError(f"未配置 {self.provider} 的 API Key")

        return AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(self, system_prompt: str, user_message: str, **kwargs) -> str:
        """调用 LLM 进行对话"""
        model = kwargs.pop("model", "gpt-4o")

        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            **kwargs,
        )
        return response.choices[0].message.content
