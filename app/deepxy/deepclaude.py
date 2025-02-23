"""DeepClaude 服务，用于协调 DeepSeek 和 Qwen 模型的调用"""

import asyncio
import json
import time
from typing import AsyncGenerator, Tuple

from app.clients import DeepSeekClient, QwenClient
from app.utils.logger import logger


class DeepClaude:
    """处理 DeepSeek 和 Qwen 模型的流式输出衔接"""

    # 不同模型的提示词模板
    PROMPT_TEMPLATES = {
        "default": """
Here's my original input:
{original_content}

Here's my another model's reasoning process:
{reasoning}

Based on this reasoning, provide your response directly to me:""",
        
        "google/": """
Original Query:
{original_content}

Reasoning Analysis:
{reasoning}

Instructions: Based on the above reasoning, generate a comprehensive response. Focus on accuracy and clarity.""",
        
        "anthropic/": """
[Previous Analysis]
{reasoning}

[Original Query]
{original_content}

[Task]
Using the above analysis, provide a detailed and well-structured response. Maintain a professional tone and ensure factual accuracy.""",
        
        "qwen": """
原始问题：
{original_content}

推理过程：
{reasoning}

请基于以上推理过程，给出完整的回答。注意保持语言的流畅性和专业性。""",
        
        "meta/": """
Input: {original_content}

Reasoning:
{reasoning}

Task: Synthesize the above reasoning into a coherent response. Prioritize clarity and logical flow.""",
        
        "mistral/": """
Context:
- Original query: {original_content}
- Reasoning provided: {reasoning}

Generate a response that:
1. Incorporates the reasoning insights
2. Addresses the original query directly
3. Maintains a clear and concise style""",
    }

    def __init__(
        self,
        deepseek_api_key: str,
        qwen_api_key: str,
        deepseek_api_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        qwen_api_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        is_origin_reasoning: bool = True,
    ):
        """初始化 API 客户端

        Args:
            deepseek_api_key: DeepSeek API Key
            qwen_api_key: Qwen API Key
            deepseek_api_url: DeepSeek API地址
            qwen_api_url: Qwen API地址
            is_origin_reasoning: 是否使用原生推理
        """
        self.deepseek_client = DeepSeekClient(
            deepseek_api_key, deepseek_api_url
        )
        self.qwen_client = QwenClient(
            qwen_api_key, qwen_api_url
        )
        self.is_origin_reasoning = is_origin_reasoning

    def _get_prompt_template(self, model: str) -> str:
        """根据模型名称获取对应的提示词模板

        Args:
            model: 模型名称

        Returns:
            str: 提示词模板
        """
        # 检查是否是特定模型
        for prefix in self.PROMPT_TEMPLATES:
            if model.startswith(prefix):
                return self.PROMPT_TEMPLATES[prefix]
        
        # 如果是通义千问模型
        if "qwen" in model.lower():
            return self.PROMPT_TEMPLATES["qwen"]
        
        # 默认模板
        return self.PROMPT_TEMPLATES["default"]

    def _format_prompt(self, model: str, original_content: str, reasoning: str) -> str:
        """格式化提示词

        Args:
            model: 模型名称
            original_content: 原始内容
            reasoning: 推理内容

        Returns:
            str: 格式化后的提示词
        """
        template = self._get_prompt_template(model)
        return template.format(
            original_content=original_content,
            reasoning=reasoning
        )

    async def chat_completions_with_stream(
        self,
        messages: list,
        model_arg: Tuple[float, float, float, float],
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
                deepseek_messages = messages.copy()
                async for content_type, content in self.deepseek_client.stream_chat(
                    deepseek_messages, deepseek_model, self.is_origin_reasoning
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
                        await qwen_queue.put(("".join(reasoning_content), content))
                        break
            except Exception as e:
                logger.error(f"处理 DeepSeek 流时发生错误: {e}")
                await qwen_queue.put(("", ""))
            # 用 None 标记 DeepSeek 任务结束
            logger.info("DeepSeek 任务处理完成，标记结束")
            await output_queue.put(None)

        async def process_qwen():
            try:
                logger.info("等待获取 DeepSeek 的推理内容...")
                reasoning, deepseek_content = await qwen_queue.get()
                logger.debug(
                    f"获取到推理内容，内容长度：{len(reasoning) if reasoning else 0}"
                )
                if not reasoning:
                    logger.warning("未能获取到有效的推理内容，将使用默认提示继续")
                    reasoning = "获取推理内容失败"

                # 构造 Qwen 的输入消息
                qwen_messages = messages.copy()
                
                # 处理可能 messages 内存在 role = system 的情况
                qwen_messages = [
                    message
                    for message in qwen_messages
                    if message.get("role", "") != "system"
                ]

                # 检查过滤后的消息列表是否为空
                if not qwen_messages:
                    raise ValueError("消息列表为空，无法处理 Qwen 请求")

                # 获取最后一个用户消息的内容
                last_user_message = None
                for message in reversed(qwen_messages):
                    if message.get("role") == "user":
                        last_user_message = message
                        break

                if not last_user_message:
                    raise ValueError("未找到用户消息，无法处理请求")

                # 修改最后一个用户消息的内容
                original_content = last_user_message["content"]
                fixed_content = self._format_prompt(qwen_model, original_content, reasoning)
                
                # 创建新的消息列表，确保最后一个消息是用户消息
                new_messages = []
                for message in qwen_messages:
                    if message == last_user_message:
                        continue
                    new_messages.append(message)
                
                # 添加DeepSeek的回答（如果有）
                if deepseek_content:
                    new_messages.append({'role': 'assistant', 'content': deepseek_content})
                
                # 添加修改后的用户消息作为最后一条消息
                new_messages.append({'role': 'user', 'content': fixed_content})

                logger.info(f"开始处理 Qwen 流，使用模型: {qwen_model}")
                logger.debug(f"Qwen 消息列表: {new_messages}")

                async for content_type, content in self.qwen_client.stream_chat(
                    messages=new_messages,
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
                                    "delta": {
                                        "role": "assistant",
                                        "content": content,
                                        "reasoning_content": "",
                                    },
                                }
                            ],
                        }
                        await output_queue.put(
                            f"data: {json.dumps(response)}\n\n".encode("utf-8")
                        )
            except Exception as e:
                logger.error(f"处理 Qwen 流时发生错误: {e}")
                logger.exception(e)  # 打印完整的错误堆栈
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
        deepseek_content = ""

        # 1. 获取 DeepSeek 的推理内容（仍然使用流式）
        try:
            deepseek_messages = messages.copy()
            async for content_type, content in self.deepseek_client.stream_chat(
                deepseek_messages, deepseek_model, self.is_origin_reasoning
            ):
                if content_type == "reasoning":
                    reasoning_content.append(content)
                elif content_type == "content":
                    deepseek_content = content
                    break
        except Exception as e:
            logger.error(f"获取 DeepSeek 推理内容时发生错误: {e}")
            reasoning_content = ["获取推理内容失败"]

        # 2. 构造 Qwen 的输入消息
        reasoning = "".join(reasoning_content)
        qwen_messages = messages.copy()
        if deepseek_content:
            qwen_messages.append({'role': 'assistant', 'content': deepseek_content})

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
        fixed_content = self._format_prompt(qwen_model, original_content, reasoning)
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
