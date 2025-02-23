"""阿里百炼 API 客户端"""

import json
from typing import AsyncGenerator
import time
from app.utils.logger import logger
from .base_client import BaseClient

class BaiLianClient(BaseClient):
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    ):
        """初始化阿里百炼客户端

        Args:
            api_key: 阿里百炼 API Key
            api_url: API地址
        """
        self.api_key = api_key
        self.api_url = api_url

    async def stream_chat(
        self,
        messages: list,
        model: str = "deepseek-r1",
        is_origin_reasoning: bool = True,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话

        Args:
            messages: 消息列表
            model: 模型名称
            is_origin_reasoning: 是否使用原生推理

        Yields:
            tuple[str, str]: (内容类型, 内容)
                内容类型: "reasoning" 或 "content"
                内容: 实际的文本内容
        """
        # 1. 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 2. 准备请求体
        request_body = {
            "model": model,
            "messages": messages,
            "stream": True,
            "result_format": "message",
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "repetition_penalty": 1.0,
                "enable_search": False
            }
        }

        logger.debug(f"发送请求到 {self.api_url}，请求体：{request_body}")

        # 3. 发送请求并处理响应
        async for chunk in self._make_request(headers, request_body, self.api_url):
            chunk_str = chunk.decode("utf-8")
            logger.debug(f"收到响应：{chunk_str}")

            try:
                lines = chunk_str.splitlines()
                for line in lines:
                    if line.startswith("data: "):
                        json_str = line[len("data: "):]
                        if json_str == "[DONE]":
                            return

                        data = json.loads(json_str)
                        if data.get("output") and data["output"].get("choices"):
                            choice = data["output"]["choices"][0]
                            if choice.get("message"):
                                if choice["message"].get("reasoning_content"):
                                    yield "reasoning", choice["message"]["reasoning_content"]
                                if choice["message"].get("content"):
                                    yield "content", choice["message"]["content"]

            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析错误: {e}")
            except Exception as e:
                logger.error(f"处理响应时发生错误: {e}")