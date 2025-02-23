"""日志记录模块"""

import logging
import os
import sys
import time
import uuid
from typing import Optional
import colorlog

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

class RequestIdFilter(logging.Filter):
    """请求ID过滤器"""
    
    _request_id: Optional[str] = None
    
    @classmethod
    def get_request_id(cls) -> str:
        """获取当前请求ID，如果不存在则创建"""
        if cls._request_id is None:
            cls._request_id = str(uuid.uuid4())
        return cls._request_id
    
    @classmethod
    def set_request_id(cls, request_id: str):
        """设置请求ID"""
        cls._request_id = request_id
    
    @classmethod
    def clear_request_id(cls):
        """清除请求ID"""
        cls._request_id = None
    
    def filter(self, record):
        """添加请求ID到日志记录"""
        record.request_id = self.get_request_id()
        return True

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self):
        """配置日志记录器"""
        # 获取环境变量中的日志级别
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = LOG_LEVELS.get(log_level, logging.INFO)
        
        # 如果已经配置过，直接返回
        if self.logger.handlers:
            return
            
        self.logger.setLevel(level)
        
        # 添加请求ID过滤器
        request_id_filter = RequestIdFilter()
        self.logger.addFilter(request_id_filter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # 日志格式
        log_colors = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
        
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(request_id)s] %(levelname)s %(name)s: %(message)s",
            log_colors=log_colors,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        log_file = os.getenv("LOG_FILE")
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                "%(asctime)s [%(request_id)s] %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def _log(self, level: int, msg: str, *args, **kwargs):
        """统一的日志记录方法"""
        extra = kwargs.pop("extra", {})
        # 添加时间戳
        extra["timestamp"] = int(time.time())
        self.logger.log(level, msg, *args, extra=extra, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """记录异常信息"""
        kwargs["exc_info"] = True
        self._log(logging.ERROR, msg, *args, **kwargs)

# 创建全局日志记录器实例
logger = StructuredLogger("deepxy")
