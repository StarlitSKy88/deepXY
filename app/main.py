import os
import sys

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.deepxy.deepxy import DeepXY
from app.utils.auth import verify_api_key
from app.utils.logger import logger

# 加载环境变量
load_dotenv()

app = FastAPI(title="DeepXY API")

# 从环境变量获取 CORS配置, API 密钥、地址以及模型名称
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*")

# DashScope 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = os.getenv("DASHSCOPE_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")

# 模型配置
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-r1")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen2.5-14b-instruct-1m")

IS_ORIGIN_REASONING = os.getenv("IS_ORIGIN_REASONING", "True").lower() == "true"

# 检查环境变量状态
logger.info(f"DASHSCOPE_API_KEY环境变量状态: {'已设置' if DASHSCOPE_API_KEY else '未设置'}")

# CORS设置
allow_origins_list = ALLOW_ORIGINS.split(",") if ALLOW_ORIGINS else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建 DeepXY 实例
if not DASHSCOPE_API_KEY:
    logger.critical("请设置环境变量 DASHSCOPE_API_KEY")
    sys.exit(1)

deep_xy = DeepXY(
    DASHSCOPE_API_KEY,
    DASHSCOPE_API_KEY,
    DASHSCOPE_API_URL,
    DASHSCOPE_API_URL,
    IS_ORIGIN_REASONING,
)

# 验证日志级别
logger.debug("当前日志级别为 DEBUG")
logger.info("开始请求")

@app.get("/")
async def root():
    logger.info("访问了根路径")
    return {"message": "Welcome to DeepXY API"}

@app.get("/v1/models")
async def list_models():
    """
    获取可用模型列表
    返回格式遵循 OpenAI API 标准
    """
    models = [
        {
            "id": "deepxy",
            "object": "model",
            "created": 1677610602,
            "owned_by": "deepxy",
            "permission": [
                {
                    "id": "modelperm-deepxy",
                    "object": "model_permission",
                    "created": 1677610602,
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False,
                }
            ],
            "root": "deepxy",
            "parent": None,
        }
    ]

    return {"object": "list", "data": models}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """处理聊天完成请求，支持流式和非流式输出

    请求体格式应与 OpenAI API 保持一致，包含：
    - messages: 消息列表
    - model: 模型名称（可选）
    - stream: 是否使用流式输出（可选，默认为 True)
    - temperature: 随机性 (可选)
    - top_p: top_p (可选)
    - presence_penalty: 话题新鲜度（可选）
    - frequency_penalty: 频率惩罚度（可选）
    """

    try:
        # 1. 获取基础信息
        body = await request.json()
        messages = body.get("messages")

        # 获取模型id
        body_model = body.get("model", "qwen2.5-14b-instruct-1m")
        qwen_model = QWEN_MODEL if QWEN_MODEL != "" else body_model

        # 2. 获取并验证参数
        model_arg = get_and_validate_params(body)
        stream = model_arg[4]  # 获取 stream 参数

        # 3. 根据 stream 参数返回相应的响应
        if stream:
            return StreamingResponse(
                deep_xy.chat_completions_with_stream(
                    messages=messages,
                    model_arg=model_arg[:4],  # 不传递 stream 参数
                    deepseek_model=DEEPSEEK_MODEL,
                    qwen_model=qwen_model,
                ),
                media_type="text/event-stream",
            )
        else:
            # 非流式输出
            response = await deep_xy.chat_completions_without_stream(
                messages=messages,
                model_arg=model_arg[:4],  # 不传递 stream 参数
                deepseek_model=DEEPSEEK_MODEL,
                qwen_model=qwen_model,
            )
            return response

    except Exception as e:
        logger.error(f"处理请求时发生错误: {e}")
        return {"error": str(e)}

def get_and_validate_params(body):
    """提取获取和验证请求参数的函数"""
    temperature: float = body.get("temperature", 0.7)
    top_p: float = body.get("top_p", 0.95)
    presence_penalty: float = body.get("presence_penalty", 0.0)
    frequency_penalty: float = body.get("frequency_penalty", 0.0)
    stream: bool = body.get("stream", True)

    # 验证温度参数
    if not isinstance(temperature, (float)) or temperature < 0.0 or temperature > 1.0:
        raise ValueError("temperature 必须在 0 到 1 之间")

    return (temperature, top_p, presence_penalty, frequency_penalty, stream)
