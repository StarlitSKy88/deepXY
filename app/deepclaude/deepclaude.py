"""DeepClaude 服务，用于协调阿里百炼的 DeepSeek 和 Qwen 模型的调用"""

import asyncio
import json
import time
from typing import AsyncGenerator

import tiktoken

from app.clients import BaiLianClient, QwenClient
from app.utils.logger import logger


class DeepClaude:
    """处理阿里百炼的 DeepSeek 和 Qwen 模型的流式输出衔接"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        deepseek_api_url: str = "https://bailian.aliyuncs.com/v2/app/completions",
        qwen_api_url: str = "https://bailian.aliyuncs.com/v2/app/completions",
        agent_key: str = None,
        is_origin_reasoning: bool = True,
    ):
        """初始化 API 客户端

        Args:
            access_key_id: 阿里云 AccessKey ID
            access_key_secret: 阿里云 AccessKey Secret
            deepseek_api_url: DeepSeek API地址
            qwen_api_url: Qwen API地址
            agent_key: 应用 Key
            is_origin_reasoning: 是否使用原生推理
        """
        self.deepseek_client = BaiLianClient(
            access_key_id, access_key_secret, deepseek_api_url, agent_key
        )
        self.qwen_client = QwenClient(
            access_key_id, access_key_secret, qwen_api_url, agent_key
        )
        self.is_origin_reasoning = is_origin_reasoning

    async def chat_completions_with_stream(
        self,
        messages: list,
        model_arg: tuple[float, float, float, float],
        deepseek_model: str = "deepseek-r1",
        qwen_model: str = "qwen2.5-14b-instruct-1m",
    ) -> AsyncGenerator[bytes, None]:
        """处理完整的流式输出过程

        Args:
            messages: 初始消息列表
            model_arg: 模型参数
            deepseek_model: DeepSeek 模型名称
            qwen_model: Qwen 模型名称

        Yields:
            字节流数据，格式如下：
            {
                "id": "chatcmpl-xxx",
                "object": "chat.completion.chunk",
                "created": timestamp,
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "reasoning_content": reasoning_content,
                        "content": content
                    }
                }]
            }
        """
        # 生成唯一的会话ID和时间戳
        chat_id = f"chatcmpl-{hex(int(time.time() * 1000))[2:]}"
        created_time = int(time.time())

        # 创建队列，用于收集输出数据
        output_queue = asyncio.Queue()
        # 队列，用于传递 DeepSeek 推理内容给 Qwen
        qwen_queue = asyncio.Queue()

        # 用于存储 DeepSeek 的推理累积内容
        reasoning_content = []

        async def process_deepseek():
            logger.info(f"开始处理 DeepSeek 流，使用模型：{deepseek_model}")
            try:
                async for content_type, content in self.deepseek_client.stream_chat(
                    messages, deepseek_model, self.is_origin_reasoning
                ):
                    if content_type == "reasoning":
                        reasoning_content.append(content)
                        response = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": deepseek_model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "role": "assistant",
                                        "reasoning_content": content,
                                        "content": "",
                                    },
                                }
                            ],
                        }
                        await output_queue.put(
                            f"data: {json.dumps(response)}\n\n".encode("utf-8")
                        )
                    elif content_type == "content":
                        # 当收到 content 类型时，将完整的推理内容发送到 qwen_queue，并结束 DeepSeek 流处理
                        logger.info(
                            f"DeepSeek 推理完成，收集到的推理内容长度：{len(''.join(reasoning_content))}"
                        )
                        await qwen_queue.put("".join(reasoning_content))
                        break
            except Exception as e:
                logger.error(f"处理 DeepSeek 流时发生错误: {e}")
                await qwen_queue.put("")
            # 用 None 标记 DeepSeek 任务结束
            logger.info("DeepSeek 任务处理完成，标记结束")
            await output_queue.put(None)

        async def process_qwen():
            try:
                logger.info("等待获取 DeepSeek 的推理内容...")
                reasoning = await qwen_queue.get()
                logger.debug(
                    f"获取到推理内容，内容长度：{len(reasoning) if reasoning else 0}"
                )
                if not reasoning:
                    logger.warning("未能获取到有效的推理内容，将使用默认提示继续")
                    reasoning = "获取推理内容失败"

                # 构造 Qwen 的输入消息
                qwen_messages = messages.copy()
                combined_content = f"""
                Here's my another model's reasoning process:\n{reasoning}\n\n
                Based on this reasoning, provide your response directly to me:"""

                # 处理可能 messages 内存在 role = system 的情况
                qwen_messages = [
                    message
                    for message in qwen_messages
                    if message.get("role", "") != "system"
                ]

                # 检查过滤后的消息列表是否为空
                if not qwen_messages:
                    raise ValueError("消息列表为空，无法处理 Qwen 请求")

                # 获取最后一个消息并检查其角色
                last_message = qwen_messages[-1]
                if last_message.get("role", "") != "user":
                    raise ValueError("最后一个消息的角色不是用户，无法处理请求")

                # 修改最后一个消息的内容
                original_content = last_message["content"]
                fixed_content = f"Here's my original input:\n{original_content}\n\n{combined_content}"
                last_message["content"] = fixed_content

                logger.info(f"开始处理 Qwen 流，使用模型: {qwen_model}")

                async for content_type, content in self.qwen_client.stream_chat(
                    messages=qwen_messages,
                    model_arg=model_arg,
                    model=qwen_model,
                ):
                    if content_type == "answer":
                        response = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": qwen_model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"role": "assistant", "content": content},
                                }
                            ],
                        }
                        await output_queue.put(
                            f"data: {json.dumps(response)}\n\n".encode("utf-8")
                        )
            except Exception as e:
                logger.error(f"处理 Qwen 流时发生错误: {e}")
            # 用 None 标记 Qwen 任务结束
            logger.info("Qwen 任务处理完成，标记结束")
            await output_queue.put(None)

        # 创建并发任务
        asyncio.create_task(process_deepseek())
        asyncio.create_task(process_qwen())

        # 等待两个任务完成，通过计数判断
        finished_tasks = 0
        while finished_tasks < 2:
            item = await output_queue.get()
            if item is None:
                finished_tasks += 1
            else:
                yield item

        # 发送结束标记
        yield b"data: [DONE]\n\n"

    async def chat_completions_without_stream(
        self,
        messages: list,
        model_arg: tuple[float, float, float, float],
        deepseek_model: str = "deepseek-r1",
        qwen_model: str = "qwen2.5-14b-instruct-1m",
    ) -> dict:
        """处理非流式输出过程

        Args:
            messages: 初始消息列表
            model_arg: 模型参数
            deepseek_model: DeepSeek 模型名称
            qwen_model: Qwen 模型名称

        Returns:
            dict: OpenAI 格式的完整响应
        """
        chat_id = f"chatcmpl-{hex(int(time.time() * 1000))[2:]}"
        created_time = int(time.time())
        reasoning_content = []

        # 1. 获取 DeepSeek 的推理内容（仍然使用流式）
        try:
            async for content_type, content in self.deepseek_client.stream_chat(
                messages, deepseek_model, self.is_origin_reasoning
            ):
                if content_type == "reasoning":
                    reasoning_content.append(content)
                elif content_type == "content":
                    break
        except Exception as e:
            logger.error(f"获取 DeepSeek 推理内容时发生错误: {e}")
            reasoning_content = ["获取推理内容失败"]

        # 2. 构造 Qwen 的输入消息
        reasoning = "".join(reasoning_content)
        qwen_messages = messages.copy()

        combined_content = f"""
            Here's my another model's reasoning process:\n{reasoning}\n\n
            Based on this reasoning, provide your response directly to me:"""

        # 处理可能 messages 内存在 role = system 的情况
        qwen_messages = [
            message
            for message in qwen_messages
            if message.get("role", "") != "system"
        ]

        # 检查过滤后的消息列表是否为空
        if not qwen_messages:
            raise ValueError("消息列表为空，无法处理 Qwen 请求")

        # 获取最后一个消息并检查其角色
        last_message = qwen_messages[-1]
        if last_message.get("role", "") != "user":
            raise ValueError("最后一个消息的角色不是用户，无法处理请求")

        # 修改最后一个消息的内容
        original_content = last_message["content"]
        fixed_content = f"Here's my original input:\n{original_content}\n\n{combined_content}"
        last_message["content"] = fixed_content

        # 3. 获取 Qwen 的回答
        qwen_response = ""
        try:
            async for content_type, content in self.qwen_client.stream_chat(
                messages=qwen_messages,
                model_arg=model_arg,
                model=qwen_model,
            ):
                if content_type == "answer":
                    qwen_response += content
        except Exception as e:
            logger.error(f"获取 Qwen 回答时发生错误: {e}")
            qwen_response = "获取回答失败"

        # 4. 构造完整的响应
        response = {
            "id": chat_id,
            "object": "chat.completion",
            "created": created_time,
            "model": qwen_model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": qwen_response,
                        "reasoning_content": reasoning,
                    },
                }
            ],
        }

        return response
