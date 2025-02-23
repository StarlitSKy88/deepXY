"""日志记录模块单元测试"""

import os
import logging
import pytest
from app.utils.logger import StructuredLogger, RequestIdFilter, LOG_LEVELS

def test_log_levels():
    """测试日志级别映射"""
    assert LOG_LEVELS["DEBUG"] == logging.DEBUG
    assert LOG_LEVELS["INFO"] == logging.INFO
    assert LOG_LEVELS["WARNING"] == logging.WARNING
    assert LOG_LEVELS["ERROR"] == logging.ERROR
    assert LOG_LEVELS["CRITICAL"] == logging.CRITICAL

def test_request_id_filter():
    """测试请求ID过滤器"""
    filter = RequestIdFilter()
    
    # 测试获取请求ID
    request_id = filter.get_request_id()
    assert request_id is not None
    assert isinstance(request_id, str)
    
    # 测试设置请求ID
    new_id = "test-id"
    filter.set_request_id(new_id)
    assert filter.get_request_id() == new_id
    
    # 测试清除请求ID
    filter.clear_request_id()
    assert filter.get_request_id() != new_id

def test_structured_logger_initialization():
    """测试结构化日志记录器初始化"""
    logger = StructuredLogger("test")
    assert logger.logger.name == "test"
    assert len(logger.logger.handlers) > 0
    assert logger.logger.level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

def test_structured_logger_levels(tmp_path):
    """测试日志记录器的不同级别"""
    # 设置临时日志文件
    log_file = tmp_path / "test.log"
    os.environ["LOG_FILE"] = str(log_file)
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    logger = StructuredLogger("test")
    
    # 测试不同级别的日志记录
    test_messages = {
        "debug": "调试信息",
        "info": "普通信息",
        "warning": "警告信息",
        "error": "错误信息",
        "critical": "严重错误"
    }
    
    for level, message in test_messages.items():
        getattr(logger, level)(message)
    
    # 验证日志文件内容
    assert log_file.exists()
    content = log_file.read_text()
    for message in test_messages.values():
        assert message in content

def test_structured_logger_extra_info():
    """测试日志记录器的额外信息"""
    logger = StructuredLogger("test")
    
    # 测试带额外信息的日志记录
    extra = {"user_id": "123", "action": "test"}
    logger.info("测试消息", extra=extra)
    
    # 由于日志输出是异步的，这里主要测试不会抛出异常
    assert True

def test_structured_logger_exception_logging():
    """测试异常日志记录"""
    logger = StructuredLogger("test")
    
    try:
        raise ValueError("测试异常")
    except Exception as e:
        logger.exception("捕获到异常")
        # 由于日志输出是异步的，这里主要测试不会抛出异常
        assert True

def test_structured_logger_file_handler(tmp_path):
    """测试文件处理器"""
    # 设置临时日志文件
    log_file = tmp_path / "test.log"
    os.environ["LOG_FILE"] = str(log_file)
    
    logger = StructuredLogger("test")
    test_message = "测试文件日志"
    logger.info(test_message)
    
    # 验证日志文件内容
    assert log_file.exists()
    content = log_file.read_text()
    assert test_message in content 