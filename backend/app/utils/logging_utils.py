"""
日志配置工具

提供统一的日志格式，包含时间戳、级别、模块名。
修复 Windows 下 GBK 编码导致中文日志输出失败的问题。
"""

import io
import logging
import sys

from app.core.config import settings


class _SafeStreamHandler(logging.StreamHandler):
    """使用 UTF-8 编码的流处理器，避免 Windows GBK 编码错误"""

    def __init__(self):
        # 使用 io.TextIOWrapper 包装 stdout，强制 UTF-8 编码
        stream = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8",
            errors="replace",
            line_buffering=True,
        )
        super().__init__(stream)


def setup_logging() -> None:
    """配置应用日志"""
    handler = _SafeStreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """获取命名日志器"""
    return logging.getLogger(name)
