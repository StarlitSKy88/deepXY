"""重试机制模块单元测试"""

import pytest
import asyncio
from app.utils.retry import RetryConfig, retry
from app.utils.errors import APIError, TimeoutError

def test_retry_config():
    """测试重试配置"""
    config = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True
    )
    
    assert config.max_retries == 3
    assert config.base_delay == 1.0
    assert config.max_delay == 10.0
    assert config.exponential_base == 2.0
    assert config.jitter is True

def test_calculate_delay():
    """测试延迟时间计算"""
    config = RetryConfig(
        base_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=False
    )
    
    # 测试指数退避
    assert config.calculate_delay(0) == 1.0  # 1 * (2^0)
    assert config.calculate_delay(1) == 2.0  # 1 * (2^1)
    assert config.calculate_delay(2) == 4.0  # 1 * (2^2)
    
    # 测试最大延迟限制
    assert config.calculate_delay(5) == 10.0  # 应该被限制在最大值

def test_retry_with_jitter():
    """测试随机抖动"""
    config = RetryConfig(
        base_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True
    )
    
    delays = [config.calculate_delay(1) for _ in range(5)]
    # 验证抖动导致的随机性
    assert len(set(delays)) > 1

@pytest.mark.asyncio
async def test_retry_success():
    """测试重试成功场景"""
    attempts = 0
    
    @retry(max_retries=3, base_delay=0.1)
    async def success_after_retry():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise APIError("测试错误")
        return "成功"
    
    result = await success_after_retry()
    assert result == "成功"
    assert attempts == 2

@pytest.mark.asyncio
async def test_retry_max_attempts():
    """测试达到最大重试次数"""
    attempts = 0
    
    @retry(max_retries=3, base_delay=0.1)
    async def always_fail():
        nonlocal attempts
        attempts += 1
        raise APIError("始终失败")
    
    with pytest.raises(APIError):
        await always_fail()
    assert attempts == 4  # 初始尝试 + 3次重试

@pytest.mark.asyncio
async def test_retry_unretryable_error():
    """测试不可重试的错误"""
    attempts = 0
    
    @retry(max_retries=3, base_delay=0.1)
    async def raise_value_error():
        nonlocal attempts
        attempts += 1
        raise ValueError("不可重试的错误")
    
    with pytest.raises(ValueError):
        await raise_value_error()
    assert attempts == 1  # 只尝试一次

@pytest.mark.asyncio
async def test_retry_callback():
    """测试重试回调函数"""
    callback_count = 0
    
    def on_retry(error, attempt):
        nonlocal callback_count
        callback_count += 1
    
    @retry(max_retries=2, base_delay=0.1, on_retry=on_retry)
    async def fail_with_callback():
        raise APIError("测试回调")
    
    with pytest.raises(APIError):
        await fail_with_callback()
    assert callback_count == 2  # 两次重试，两次回调

@pytest.mark.asyncio
async def test_retry_multiple_errors():
    """测试多种错误类型"""
    attempts = 0
    
    @retry(max_retries=3, base_delay=0.1)
    async def raise_different_errors():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise APIError("API错误")
        elif attempts == 2:
            raise TimeoutError("超时错误")
        elif attempts == 3:
            return "成功"
        raise Exception("不应该到达这里")
    
    result = await raise_different_errors()
    assert result == "成功"
    assert attempts == 3 