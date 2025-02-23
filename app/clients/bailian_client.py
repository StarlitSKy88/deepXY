"""阿里百炼 API 客户端"""

import json
from typing import AsyncGenerator
import time
import hmac
import base64
import uuid
import hashlib
from urllib.parse import urlencode

from app.utils.logger import logger
from .base_client import BaseClient

class BaiLianClient(BaseClient):
    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        api_url: str = "https://bailian.aliyuncs.com/v2/app/completions",
        agent_key: str = None,
    ):
        """初始化阿里百炼客户端

        Args:
            access_key_id: 阿里云 AccessKey ID
            access_key_secret: 阿里云 AccessKey Secret
            api_url: API地址
            agent_key: 应用 Key
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.api_url = api_url
        self.agent_key = agent_key

    def _generate_signature(self, params):
        """生成签名"""
        # 1. 按照参数名称的字典顺序排序
        sorted_params = sorted(params.items())
        
        # 2. 将参数名称和参数值用 = 连接，并用 & 连接所有参数
        canonicalized_query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        
        # 3. 计算签名
        string_to_sign = canonicalized_query_string.encode('utf-8')
        secret = self.access_key_secret.encode('utf-8')
        signature = base64.b64encode(
            hmac.new(secret, string_to_sign, hashlib.sha1).digest()
        ).decode('utf-8')
        
        return signature

    def _get_common_params(self):
        """获取公共参数"""
        params = {
            "AccessKeyId": self.access_key_id,
            "Format": "JSON",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "Version": "2023-06-01",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "SignatureNonce": str(uuid.uuid4()),
        }
        return params

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
        # 1. 准备请求参数
        params = self._get_common_params()
        
        # 2. 准备请求体
        request_body = {
            "model": model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "stream": True,
                "incremental_output": True
            }
        }
        
        if self.agent_key:
            request_body["agent_key"] = self.agent_key

        # 3. 生成签名
        signature = self._generate_signature(params)
        params["Signature"] = signature

        # 4. 构建完整的URL
        url = f"{self.api_url}?{urlencode(params)}"

        # 5. 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        # 6. 发送请求并处理响应
        accumulated_content = ""
        is_collecting_think = False

        async for chunk in self._make_request(headers, request_body, url):
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
                            
                            if is_origin_reasoning:
                                # 处理原生推理内容
                                if "<think>" in content and not is_collecting_think:
                                    is_collecting_think = True
                                    yield "reasoning", content
                                elif is_collecting_think:
                                    if "</think>" in content:
                                        is_collecting_think = False
                                        yield "reasoning", content
                                        yield "content", ""
                                    else:
                                        yield "reasoning", content
                                else:
                                    yield "content", content
                            else:
                                # 直接输出内容
                                yield "content", content

            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析错误: {e}")
            except Exception as e:
                logger.error(f"处理响应时发生错误: {e}") 