"""
独立的 LLM 客户端 - 从 comfyui-twitterchat 提取
支持 OpenAI/Claude/本地模型
"""
import asyncio
import json
import time
from typing import List, Dict, Optional

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("[LLM Client] 警告: 未安装 openai 库")

import aiohttp


class AsyncLLMClient:
    """异步 LLM 客户端 - 支持高并发"""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4"
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip('/')
        self.model = model

        # 使用异步 OpenAI SDK
        if HAS_OPENAI:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=api_base,
                max_retries=3,
                timeout=180.0
            )
            self.use_sdk = True
        else:
            self.client = None
            self.use_sdk = False

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 3000,
        timeout: int = 180
    ) -> str:
        """
        异步生成文本

        Args:
            messages: 消息列表 [{"role": "system", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间（秒）

        Returns:
            生成的文本
        """
        if self.use_sdk:
            return await self._generate_with_sdk(messages, temperature, max_tokens)
        else:
            return await self._generate_with_aiohttp(messages, temperature, max_tokens, timeout)

    async def _generate_with_sdk(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """使用 OpenAI SDK 异步生成"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"LLM 调用失败: {e}")

    async def _generate_with_aiohttp(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        timeout: int
    ) -> str:
        """使用 aiohttp 异步调用"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"LLM API 错误 {resp.status}: {error_text}")

                data = await resp.json()
                return data["choices"][0]["message"]["content"]


class LLMClientPool:
    """LLM 客户端池 - 支持并发限流"""

    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str,
        max_concurrent: int = 10
    ):
        self.client = AsyncLLMClient(api_key, api_base, model)
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def generate(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 3000
    ) -> str:
        """带并发限制的生成"""
        async with self.semaphore:
            return await self.client.generate(messages, temperature, max_tokens)
