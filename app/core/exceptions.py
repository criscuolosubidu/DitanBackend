"""
自定义异常模块
"""
from typing import Any, Optional


class BaseAPIException(Exception):
    """基础 API 异常类"""
    
    def __init__(
        self,
        status_code: int = 500,
        message: str = "服务器内部错误",
        detail: Optional[Any] = None
    ):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class ValidationException(BaseAPIException):
    """验证异常"""
    
    def __init__(self, message: str = "请求参数验证失败", detail: Optional[Any] = None):
        super().__init__(status_code=400, message=message, detail=detail)


class NotFoundException(BaseAPIException):
    """未找到异常"""
    
    def __init__(self, message: str = "资源未找到", detail: Optional[Any] = None):
        super().__init__(status_code=404, message=message, detail=detail)


class DuplicateException(BaseAPIException):
    """重复数据异常"""
    
    def __init__(self, message: str = "数据已存在", detail: Optional[Any] = None):
        super().__init__(status_code=409, message=message, detail=detail)


class DatabaseException(BaseAPIException):
    """数据库异常"""
    
    def __init__(self, message: str = "数据库操作失败", detail: Optional[Any] = None):
        super().__init__(status_code=500, message=message, detail=detail)


class InternalServerException(BaseAPIException):
    """内部服务器异常"""
    
    def __init__(self, message: str = "服务器内部错误", detail: Optional[Any] = None):
        super().__init__(status_code=500, message=message, detail=detail)

