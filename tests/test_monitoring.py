"""监控功能测试"""

import os
import asyncio
import pytest
from datetime import datetime, timedelta
from app.monitoring import ModelPerformanceMonitor, ModelFailoverHandler, ModelResponseCache

@pytest.mark.asyncio
async def test_performance_monitor():
    """测试性能监控"""
    monitor = ModelPerformanceMonitor()
    
    # 记录成功的调用
    start_time = datetime.now().timestamp()
    await monitor.record_performance(
        model="deepW",
        start_time=start_time,
        end_time=start_time + 2.0,
        token_count=100,
        success=True
    )
    
    # 记录失败的调用
    await monitor.record_performance(
        model="deepW",
        start_time=start_time,
        end_time=start_time + 1.0,
        token_count=0,
        success=False,
        error="API Error"
    )
    
    # 获取统计信息
    stats = monitor.get_model_stats("deepW")
    assert stats["total_calls"] == 2
    assert stats["success_rate"] == 0.5
    assert stats["error_rate"] == 0.5
    assert len(stats["recent_errors"]) == 1
    
@pytest.mark.asyncio
async def test_failover_handler():
    """测试回退处理"""
    handler = ModelFailoverHandler(
        models=["deepW", "deepG", "deepC"],
        max_retries=2,
        cooldown_minutes=1
    )
    
    # 测试模型切换
    model1 = await handler.get_next_model("Error 1")
    assert model1 in ["deepG", "deepC"]  # deepW应该进入冷却
    
    model2 = await handler.get_next_model("Error 2")
    assert model2 != model1  # 应该切换到下一个模型
    
    # 测试达到最大重试次数
    model3 = await handler.get_next_model("Error 3")
    assert model3 is None
    
    # 测试重置
    handler.reset()
    model4 = await handler.get_next_model()
    assert model4 is not None
    
@pytest.mark.asyncio
async def test_response_cache():
    """测试响应缓存"""
    cache = ModelResponseCache(max_size=2, ttl_minutes=1)
    
    messages = [{"role": "user", "content": "test"}]
    
    # 测试缓存设置和获取
    await cache.set(messages, "deepW", "Response 1")
    response = await cache.get(messages, "deepW")
    assert response == "Response 1"
    
    # 测试缓存过期
    await asyncio.sleep(0.1)  # 等待0.1秒
    cache.clear_expired()
    response = await cache.get(messages, "deepW")
    assert response == "Response 1"  # 0.1秒后应该还在
    
    # 测试缓存统计
    stats = cache.get_cache_stats()
    assert stats["total_items"] == 1
    assert stats["memory_usage"] > 0
    
if __name__ == "__main__":
    asyncio.run(test_performance_monitor())
    asyncio.run(test_failover_handler())
    asyncio.run(test_response_cache()) 