"""
DitanBackend 主应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.router import api_v1_router
from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.core.exceptions import BaseAPIException
from app.core.logging import LoggerSetup, get_logger, log_error

# 初始化日志
LoggerSetup()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("正在初始化数据库...")
    try:
        await init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        log_error(logger, "数据库初始化失败", e)
        raise

    yield

    # 关闭时清理资源
    logger.info("正在关闭数据库连接...")
    await close_db()
    logger.info("应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="病人数据上传后端服务",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 注册路由
app.include_router(api_v1_router)


# 全局异常处理
@app.exception_handler(BaseAPIException)
async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """处理自定义 API 异常"""
    log_error(
        logger,
        f"API 异常: {exc.message}",
        exc if settings.APP_DEBUG else None
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "detail": exc.detail if settings.APP_DEBUG else None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证异常"""
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")

    error_detail = "; ".join(error_messages)
    log_error(logger, f"请求验证失败: {error_detail}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "message": "请求参数验证失败",
            "detail": error_detail,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    log_error(logger, "未处理的异常", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "detail": str(exc) if settings.APP_DEBUG else None,
        },
    )


# 健康检查端点
@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# 根端点
@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"正在启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
