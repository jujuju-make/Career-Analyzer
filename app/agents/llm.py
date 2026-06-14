"""LLM 客户端封装（支持 OpenAI / DeepSeek / 千问，包括图片视觉能力）"""

import json
import base64
from pathlib import Path
from typing import Optional, Union, Dict, Any
from openai import AsyncOpenAI

from app.core.config import settings


class LLMClient:
    """统一的 LLM 调用客户端，支持多模型和图片输入"""

    def __init__(self, provider: str = "deepseek"):
        self.provider = provider
        self.client = self._build_client()
        self.model = self._get_model_name()

    def _build_client(self) -> AsyncOpenAI:
        """根据 provider 构建客户端"""
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

    def _get_model_name(self) -> str:
        """获取对应 provider 的模型名"""
        model_map = {
            "deepseek": "deepseek-chat",
            "qwen": "qwen3.7-plus",  # 千问模型（百炼上支持文本+图片理解）
        }
        return model_map.get(self.provider, "deepseek-chat")

    async def chat(self, system_prompt: str, user_message: str, **kwargs) -> Union[str, Dict[str, Any]]:
        """调用 LLM 进行对话"""
        model = kwargs.pop("model", self.model)
        temperature = kwargs.pop("temperature", 0.1)

        create_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
        }
        # 千问不支持 response_format 参数
        if self.provider != "qwen":
            create_kwargs["response_format"] = {"type": "json_object"}
        create_kwargs.update(kwargs)

        response = await self.client.chat.completions.create(**create_kwargs)
        
        content = response.choices[0].message.content.strip()
        
        # 尝试解析 JSON
        try:
            if content.startswith("```"):
                content = content.strip("`")
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except json.JSONDecodeError:
            return content

    async def chat_raw(self, system_prompt: str, user_message: str, **kwargs) -> str:
        """调用 LLM 进行对话，返回原始字符串（不解析 JSON）"""
        model = kwargs.pop("model", self.model)
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=kwargs.pop("temperature", 0.1),
            **kwargs,
        )

        return response.choices[0].message.content.strip()

    async def chat_with_image(
        self,
        system_prompt: str,
        user_message: str,
        image_path: Union[str, Path],
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        调用 LLM 进行对话（支持图片输入）
        
        :param system_prompt: 系统提示词
        :param user_message: 用户消息文本
        :param image_path: 图片路径（本地文件路径）
        :param kwargs: 其他参数
        :return: 解析后的 JSON 响应或原始文本
        """
        if self.provider != "qwen":
            raise ValueError("只有千问模型支持图片输入")

        # 读取图片并转换为 base64
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # 确定图片格式
        suffix = image_path.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(suffix, "image/jpeg")

        # 构建消息（支持文本 + 图片混合）
        content = [
            {"type": "text", "text": user_message},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{image_data}"
                },
            },
        ]

        model = kwargs.pop("model", self.model)
        temperature = kwargs.pop("temperature", 0.1)

        # 构建请求参数，千问不支持 response_format
        create_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "temperature": temperature,
        }
        if self.provider != "qwen":
            create_kwargs["response_format"] = {"type": "json_object"}
        create_kwargs.update(kwargs)

        response = await self.client.chat.completions.create(**create_kwargs)

        response_text = response.choices[0].message.content.strip()

        # 尝试解析 JSON
        try:
            if response_text.startswith("```"):
                response_text = response_text.strip("`")
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            return json.loads(response_text)
        except json.JSONDecodeError:
            return response_text


