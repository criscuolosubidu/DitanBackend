"""API 依赖注入"""
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db, get_current_active_doctor, get_logger
from app.models import Doctor

logger = get_logger(__name__)


class RequestContext:
    """请求上下文"""

    def __init__(self, request: Request, db: AsyncSession, doctor: Doctor = None):
        self.request = request
        self.db = db
        self.doctor = doctor
        self.endpoint = f"{request.method} {request.url.path}"

    def log_info(self, message: str):
        logger.info(f"[{self.endpoint}] {message}")

    def log_error(self, message: str, exc: Exception = None):
        if exc:
            logger.error(f"[{self.endpoint}] {message}: {exc}", exc_info=True)
        else:
            logger.error(f"[{self.endpoint}] {message}")


async def get_request_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RequestContext:
    """获取请求上下文（无需认证）"""
    return RequestContext(request=request, db=db)


async def get_auth_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_active_doctor),
) -> RequestContext:
    """获取请求上下文（需要认证）"""
    return RequestContext(request=request, db=db, doctor=doctor)

