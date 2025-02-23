from fastapi import HTTPException, Header
from typing import Optional
import os
from dotenv import load_dotenv
from app.utils.logger import logger

# 加载 .env 文件
logger.info(f"当前工作目录: {os.getcwd()}")
logger.info("尝试加载.env文件...")
load_dotenv(override=True)  # 添加override=True强制覆盖已存在的环境变量

# 获取环境变量
ALLOW_API_KEY = os.getenv("ALLOW_API_KEY")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# 检查环境变量状态
logger.info(f"DASHSCOPE_API_KEY环境变量状态: {'已设置' if DASHSCOPE_API_KEY else '未设置'}")

if not DASHSCOPE_API_KEY:
    logger.critical("请设置环境变量 DASHSCOPE_API_KEY")
    raise ValueError("DASHSCOPE_API_KEY environment variable must be set")

# 打印API密钥的前4位用于调试
logger.info(f"Loaded API key starting with: {ALLOW_API_KEY[:4] if ALLOW_API_KEY and len(ALLOW_API_KEY) >= 4 else ALLOW_API_KEY}")

async def verify_api_key(authorization: Optional[str] = Header(None)) -> None:
    """验证API密钥（已禁用）"""
    pass
