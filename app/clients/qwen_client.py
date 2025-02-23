"""阿里百炼 Qwen API 客户端"""

import json
import os
from typing import AsyncGenerator
import time
from app.utils.logger import logger
from .base_client import BaseClient

class QwenClient(BaseClient):
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    ):
        """初始化阿里百炼 Qwen 客户端

        Args:
            api_key: API Key
            api_url: API地址
        """
        super().__init__(api_key, api_url)
        # 获取 OpenRouter 配置
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_api_url = os.getenv("OPENROUTER_API_URL")

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
        # 判断是否使用 OpenRouter API
        is_openrouter = "openrouter.ai" in model or (
            model.startswith("google/") or 
            model.startswith("anthropic/") or 
            model.startswith("meta/") or 
            model.startswith("mistral/")
        )

        # 根据不同的 API 设置请求头和请求体
        if is_openrouter:
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "HTTP-Referer": "https://github.com/ErlichLiu/DeepClaude",
                "X-Title": "DeepClaude"
            }
            api_url = self.openrouter_api_url
        else:
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "Authorization": f"Bearer {self.api_key}"
            }
            api_url = self.api_url

        # 准备请求体
        temperature, top_p, presence_penalty, frequency_penalty = model_arg
        request_body = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": float(temperature),
            "top_p": float(top_p),
        }

        # 对于 OpenRouter API，添加特定参数
        if is_openrouter:
            request_body.update({
                "presence_penalty": float(presence_penalty),
                "frequency_penalty": float(frequency_penalty)
            })
        else:
            # DashScope API 特定参数
            request_body.update({
                "result_format": "message",
                "parameters": {
                    "temperature": float(temperature),
                    "top_p": float(top_p),
                    "top_k": 40,
                    "repetition_penalty": 1.0,
                    "enable_search": False
                }
            })

        logger.debug(f"发送请求到 {api_url}，请求体：{request_body}")

        # 发送请求并处理响应
        async for chunk in self._make_request(headers, request_body, api_url):
            chunk_str = chunk.decode("utf-8")
            logger.debug(f"收到响应：{chunk_str}")

            try:
                lines = chunk_str.splitlines()
                for line in lines:
                    if line.startswith("data: "):
                        json_str = line[len("data: "):]
                        if json_str == "[DONE]":
                            logger.info("收到结束标记")
                            return

                        data = json.loads(json_str)
                        logger.debug(f"解析的JSON数据：{data}")
                        
                        if is_openrouter:
                            # OpenRouter API 响应格式处理
                            if data.get("choices") and data["choices"][0].get("delta"):
                                delta = data["choices"][0]["delta"]
                                if delta.get("content"):
                                    content = delta["content"]
                                    logger.debug(f"生成内容：{content}")
                                    yield "answer", content
                        else:
                            # DashScope API 响应格式处理
                            if data.get("output") and data["output"].get("choices"):
                                choice = data["output"]["choices"][0]
                                logger.debug(f"处理choice：{choice}")
                                
                                if choice.get("message"):
                                    message = choice["message"]
                                    logger.debug(f"处理message：{message}")
                                    
                                    if message.get("content"):
                                        content = message["content"]
                                        logger.debug(f"生成内容：{content}")
                                        yield "answer", content

            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析错误: {e}")
                logger.error(f"错误的JSON字符串: {json_str}")
            except Exception as e:
                logger.error(f"处理响应时发生错误: {e}")
                logger.exception(e) 