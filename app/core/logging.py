"""
日志配置模块
"""
import logging
import sys
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class LoggerSetup:
    """日志设置类"""
    
    def __init__(self):
        self.settings = get_settings()
        self._setup_logger()
    
    def _setup_logger(self):
        """配置日志"""
        # 创建日志目录
        log_file = Path(self.settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置日志格式
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # 配置根日志记录器
        logging.basicConfig(
            level=getattr(logging, self.settings.LOG_LEVEL),
            format=log_format,
            datefmt=date_format,
            handlers=[
                # 控制台处理器
                logging.StreamHandler(sys.stdout),
                # 文件处理器
                logging.FileHandler(
                    log_file,
                    encoding="utf-8",
                    mode="a"
                )
            ]
        )
        
        # 设置第三方库日志级别
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, endpoint: str, data: Any):
    """记录请求日志"""
    logger.info(f"请求端点: {endpoint}")
    logger.info(f"请求参数: {data}")


def log_response(logger: logging.Logger, endpoint: str, data: Any):
    """记录响应日志"""
    logger.info(f"响应端点: {endpoint}")
    logger.info(f"响应数据: {data}")


def log_error(logger: logging.Logger, error_msg: str, exc: Exception = None):
    """记录错误日志"""
    if exc:
        logger.error(f"{error_msg}: {str(exc)}")
    else:
        logger.error(error_msg)

