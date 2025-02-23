"""请求重试机制模块"""

import time
import random
from functools import wraps
from typing import Type, Tuple, Optional, Callable, Any

from .errors import DeepClaudeError, APIError, TimeoutError, RateLimitError
from .logger import logger

class RetryConfig:
    """重试配置类"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_errors: Optional[Tuple[Type[Exception], ...]] = None
    ):
        """
        初始化重试配置
        
        Args:
            max_retries (int): 最大重试次数
            base_delay (float): 基础延迟时间(秒)
            max_delay (float): 最大延迟时间(秒)
            exponential_base (float): 指数退避的基数
            jitter (bool): 是否添加随机抖动
            retry_errors (tuple): 需要重试的错误类型
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        
        # 默认重试的错误类型
        self.retry_errors = retry_errors or (
            APIError,
            TimeoutError,
            RateLimitError,
            ConnectionError,
            TimeoutError
        )
    
    def calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟时间
        
        Args:
            attempt (int): 当前重试次数
            
        Returns:
            float: 延迟时间(秒)
        """
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # 添加 0-100% 的随机抖动
            delay *= (1 + random.random())
            
        return delay

def retry(
    max_retries: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    retry_errors: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int], Any]] = None
) -> Callable:
    """
    重试装饰器
    
    Args:
        max_retries (int, optional): 最大重试次数
        base_delay (float, optional): 基础延迟时间
        max_delay (float, optional): 最大延迟时间
        retry_errors (tuple, optional): 需要重试的错误类型
        on_retry (callable, optional): 重试回调函数
        
    Returns:
        Callable: 装饰器函数
    """
    config = RetryConfig(
        max_retries=max_retries if max_retries is not None else 3,
        base_delay=base_delay if base_delay is not None else 1.0,
        max_delay=max_delay if max_delay is not None else 10.0,
        retry_errors=retry_errors
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # 检查是否需要重试这个错误
                    if not isinstance(e, config.retry_errors):
                        raise
                    
                    # 最后一次尝试失败
                    if attempt == config.max_retries:
                        logger.error(
                            f"重试{config.max_retries}次后仍然失败: {str(e)}",
                            exc_info=True
                        )
                        raise
                    
                    # 计算延迟时间
                    delay = config.calculate_delay(attempt)
                    
                    # 记录重试信息
                    logger.warning(
                        f"请求失败 (尝试 {attempt + 1}/{config.max_retries}): {str(e)}. "
                        f"将在 {delay:.2f} 秒后重试"
                    )
                    
                    # 执行重试回调
                    if on_retry:
                        on_retry(e, attempt)
                    
                    # 等待后重试
                    await time.sleep(delay)
            
            # 不应该到达这里
            raise last_exception
        
        return wrapper
    
    return decorator 