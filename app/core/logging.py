"""日志配置模块"""
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from app.core.config import get_settings


class LoggerSetup:
    """日志设置类"""

    _initialized = False

    def __init__(self):
        if not LoggerSetup._initialized:
            self._setup_logger()
            LoggerSetup._initialized = True

    def _setup_logger(self):
        settings = get_settings()

        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"

        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file, encoding="utf-8", mode="a"),
            ],
        )

        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, endpoint: str, data: Any = None):
    """记录请求日志"""
    if data:
        logger.info(f"请求 {endpoint}: {data}")
    else:
        logger.info(f"请求 {endpoint}")


def log_response(logger: logging.Logger, endpoint: str, data: Any = None):
    """记录响应日志"""
    if data:
        logger.debug(f"响应 {endpoint}: {data}")
    else:
        logger.debug(f"响应 {endpoint}")


def log_error(logger: logging.Logger, message: str, exc: Optional[Exception] = None):
    """记录错误日志"""
    if exc:
        logger.error(f"{message}: {exc}", exc_info=True)
    else:
        logger.error(message)
