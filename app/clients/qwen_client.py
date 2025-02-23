"""阿里百炼 Qwen API 客户端"""

import json
from typing import AsyncGenerator
import time
from app.utils.logger import logger
from .base_client import BaseClient

class QwenClient(BaseClient):
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://bailian.aliyuncs.com/v2/app/completions",
    ):
        """初始化阿里百炼 Qwen 客户端

        Args:
            api_key: 阿里百炼 API Key
            api_url: API地址
        """
        self.api_key = api_key
        self.api_url = api_url

    async def stream_chat(
        self,
        messages: list,
        model_arg: tuple[float, float, float, float] = (0.7, 0.95, 0.0, 0.0),
        model: str = "qwen2.5-14b-instruct-1m",
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话

        Args:
            messages: 消息列表
            model_arg: 模型参数 (temperature, top_p, presence_penalty, frequency_penalty)
            model: 模型名称

        Yields:
            tuple[str, str]: (内容类型, 内容)
                内容类型: "answer"
                内容: 实际的文本内容
        """
        # 1. 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 2. 准备请求体
        temperature, top_p, presence_penalty, frequency_penalty = model_arg
        request_body = {
            "model": model,
            "messages": messages,
            "stream": True,
            "incremental_output": True,
            "temperature": temperature,
            "top_p": top_p,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty
        }

        # 3. 发送请求并处理响应
        async for chunk in self._make_request(headers, request_body, self.api_url):
            chunk_str = chunk.decode("utf-8")

            try:
                lines = chunk_str.splitlines()
                for line in lines:
                    if line.startswith("data: "):
                        json_str = line[len("data: "):]
                        if json_str == "[DONE]":
                            return

                        data = json.loads(json_str)
                        if data and data.get("output"):
                            content = data["output"].get("text", "")
                            yield "answer", content

            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析错误: {e}")
            except Exception as e:
                logger.error(f"处理响应时发生错误: {e}") 