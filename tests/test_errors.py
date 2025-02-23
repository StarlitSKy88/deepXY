"""错误处理模块单元测试"""

import pytest
from app.utils.errors import (
    DeepClaudeError,
    APIKeyError,
    ModelNotFoundError,
    InvalidRequestError,
    APIError,
    RateLimitError,
    TimeoutError,
    handle_error,
)

def test_base_error():
    """测试基础错误类"""
    error = DeepClaudeError(
        message="测试错误",
        error_code="TEST_ERROR",
        http_status=500,
        details={"test": "detail"}
    )
    assert error.message == "测试错误"
    assert error.error_code == "TEST_ERROR"
    assert error.http_status == 500
    assert error.details == {"test": "detail"}

def test_api_key_error():
    """测试API密钥错误"""
    error = APIKeyError("无效的API密钥")
    assert error.message == "无效的API密钥"
    assert error.error_code == "AUTH_ERROR"
    assert error.http_status == 401

def test_model_not_found_error():
    """测试模型不存在错误"""
    error = ModelNotFoundError("模型不存在")
    assert error.message == "模型不存在"
    assert error.error_code == "MODEL_NOT_FOUND"
    assert error.http_status == 404

def test_invalid_request_error():
    """测试请求参数错误"""
    error = InvalidRequestError("无效的请求参数")
    assert error.message == "无效的请求参数"
    assert error.error_code == "INVALID_REQUEST"
    assert error.http_status == 400

def test_api_error():
    """测试API调用错误"""
    error = APIError("API调用失败")
    assert error.message == "API调用失败"
    assert error.error_code == "API_ERROR"
    assert error.http_status == 502

def test_rate_limit_error():
    """测试请求频率限制错误"""
    error = RateLimitError("请求过于频繁")
    assert error.message == "请求过于频繁"
    assert error.error_code == "RATE_LIMIT"
    assert error.http_status == 429

def test_timeout_error():
    """测试超时错误"""
    error = TimeoutError("请求超时")
    assert error.message == "请求超时"
    assert error.error_code == "TIMEOUT"
    assert error.http_status == 504

def test_error_handling():
    """测试错误处理函数"""
    # 测试ValueError转换
    error = handle_error(ValueError("无效的值"))
    assert isinstance(error, InvalidRequestError)
    assert error.message == "无效的值"

    # 测试TimeoutError转换
    error = handle_error(TimeoutError("请求超时"))
    assert isinstance(error, TimeoutError)
    assert error.message == "请求超时"

    # 测试未知错误转换
    error = handle_error(Exception("未知错误"))
    assert isinstance(error, DeepClaudeError)
    assert error.message == "未知错误" 