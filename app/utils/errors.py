"""错误处理模块"""

from typing import Dict, Optional, Type

class DeepClaudeError(Exception):
    """DeepClaude基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        http_status: int = 500,
        details: Optional[Dict] = None
    ):
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}
        super().__init__(self.message)

class APIKeyError(DeepClaudeError):
    """API密钥相关错误"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            http_status=401,
            details=details
        )

class ModelNotFoundError(DeepClaudeError):
    """模型不存在错误"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="MODEL_NOT_FOUND",
            http_status=404,
            details=details
        )

class InvalidRequestError(DeepClaudeError):
    """请求参数错误"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="INVALID_REQUEST",
            http_status=400,
            details=details
        )

class APIError(DeepClaudeError):
    """API调用错误"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="API_ERROR",
            http_status=502,
            details=details
        )

class RateLimitError(DeepClaudeError):
    """请求频率限制错误"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT",
            http_status=429,
            details=details
        )

class TimeoutError(DeepClaudeError):
    """请求超时错误"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="TIMEOUT",
            http_status=504,
            details=details
        )

# 错误映射表
ERROR_MAPPING: Dict[Type[Exception], Type[DeepClaudeError]] = {
    ValueError: InvalidRequestError,
    TimeoutError: TimeoutError,
    ConnectionError: APIError,
    PermissionError: APIKeyError,
}

def handle_error(error: Exception) -> DeepClaudeError:
    """统一错误处理函数
    
    Args:
        error: 原始异常

    Returns:
        DeepClaudeError: 转换后的错误
    """
    error_class = ERROR_MAPPING.get(type(error), DeepClaudeError)
    if isinstance(error, DeepClaudeError):
        return error
        
    return error_class(
        message=str(error),
        details={"original_error": str(error)}
    ) 