#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块

提供统一的日志配置和管理功能,支持多种日志级别和输出格式

作者: CapCutAPI Team
创建时间: 2025-11-11
"""

import logging
import logging.handlers
import os
from typing import Optional
from datetime import datetime


# ===== 日志配置常量 =====

LOG_DIR = 'logs'
LOG_FILE = 'capcutapi.log'
ERROR_LOG_FILE = 'capcutapi_error.log'
ACCESS_LOG_FILE = 'capcutapi_access.log'

# 日志格式
DETAILED_FORMAT = '%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s'
SIMPLE_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
ACCESS_FORMAT = '%(asctime)s [ACCESS] %(message)s'

# 日志文件大小和备份数量
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


def setup_logging(
    log_level: str = 'INFO',
    log_to_console: bool = True,
    log_to_file: bool = True,
    log_dir: str = LOG_DIR
) -> logging.Logger:
    """
    配置应用程序日志系统

    Args:
        log_level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_to_console: 是否输出到控制台
        log_to_file: 是否输出到文件
        log_dir: 日志文件目录

    Returns:
        配置好的logger实例
    """
    # 创建日志目录
    if log_to_file and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 获取或创建root logger
    logger = logging.getLogger('capcutapi')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 清除已有的handlers
    logger.handlers.clear()

    # ===== 控制台输出 =====
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(SIMPLE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # ===== 文件输出（主日志） =====
    if log_to_file:
        # 主日志文件（所有级别）
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, LOG_FILE),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(DETAILED_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 错误日志文件（仅ERROR和CRITICAL）
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, ERROR_LOG_FILE),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(DETAILED_FORMAT)
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)

    # 防止日志传播到root logger
    logger.propagate = False

    return logger


def setup_access_logger(log_dir: str = LOG_DIR) -> logging.Logger:
    """
    配置访问日志记录器（用于记录API访问）

    Args:
        log_dir: 日志文件目录

    Returns:
        配置好的访问日志logger
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    access_logger = logging.getLogger('capcutapi.access')
    access_logger.setLevel(logging.INFO)
    access_logger.handlers.clear()

    # 访问日志文件
    access_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, ACCESS_LOG_FILE),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_formatter = logging.Formatter(ACCESS_FORMAT)
    access_handler.setFormatter(access_formatter)
    access_logger.addHandler(access_handler)

    # 防止传播到父logger
    access_logger.propagate = False

    return access_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取logger实例

    Args:
        name: logger名称,如果为None则返回主logger

    Returns:
        logger实例
    """
    if name:
        return logging.getLogger(f'capcutapi.{name}')
    return logging.getLogger('capcutapi')


class PerformanceLogger:
    """性能日志记录器（用于记录API执行时间）"""

    def __init__(self, logger: logging.Logger, operation: str):
        """
        初始化性能日志记录器

        Args:
            logger: logger实例
            operation: 操作名称
        """
        self.logger = logger
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        """进入上下文时开始计时"""
        self.start_time = datetime.now()
        self.logger.debug(f"开始执行: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时计算耗时"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type:
                self.logger.error(
                    f"执行失败: {self.operation} (耗时: {duration:.3f}秒)",
                    exc_info=(exc_type, exc_val, exc_tb)
                )
            else:
                self.logger.info(f"执行完成: {self.operation} (耗时: {duration:.3f}秒)")


def log_api_request(logger: logging.Logger, endpoint: str, method: str,
                    remote_addr: str, user_agent: Optional[str] = None):
    """
    记录API请求

    Args:
        logger: logger实例
        endpoint: API端点
        method: HTTP方法
        remote_addr: 客户端IP地址
        user_agent: 用户代理字符串
    """
    log_msg = f"{method} {endpoint} - IP: {remote_addr}"
    if user_agent:
        log_msg += f" - UA: {user_agent}"
    logger.info(log_msg)


def log_api_response(logger: logging.Logger, endpoint: str, status_code: int,
                     duration: float, response_size: Optional[int] = None):
    """
    记录API响应

    Args:
        logger: logger实例
        endpoint: API端点
        status_code: HTTP状态码
        duration: 请求处理时间（秒）
        response_size: 响应大小（字节）
    """
    log_msg = f"{endpoint} - 状态码: {status_code} - 耗时: {duration:.3f}秒"
    if response_size:
        log_msg += f" - 大小: {response_size} bytes"
    logger.info(log_msg)


# ===== 测试代码 =====

if __name__ == '__main__':
    print("=== 日志配置模块测试 ===\n")

    # 测试主日志
    logger = setup_logging(log_level='DEBUG')
    logger.debug("这是一条DEBUG消息")
    logger.info("这是一条INFO消息")
    logger.warning("这是一条WARNING消息")
    logger.error("这是一条ERROR消息")
    logger.critical("这是一条CRITICAL消息")

    # 测试访问日志
    access_logger = setup_access_logger()
    log_api_request(
        access_logger,
        endpoint='/create_draft',
        method='POST',
        remote_addr='127.0.0.1',
        user_agent='Mozilla/5.0'
    )
    log_api_response(
        access_logger,
        endpoint='/create_draft',
        status_code=200,
        duration=0.123,
        response_size=1024
    )

    # 测试性能日志
    import time
    with PerformanceLogger(logger, "测试操作"):
        time.sleep(0.5)

    print("\n=== 测试完成 ===")
    print(f"日志文件已创建在 {LOG_DIR} 目录下:")
    print(f"  - {LOG_FILE} (主日志)")
    print(f"  - {ERROR_LOG_FILE} (错误日志)")
    print(f"  - {ACCESS_LOG_FILE} (访问日志)")
