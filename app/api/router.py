"""
API 路由汇总
"""
from fastapi import APIRouter

from app.api.patient import router as patient_router


# 创建 v1 版本路由
api_v1_router = APIRouter(prefix="/api/v1")

# 注册各个模块的路由
api_v1_router.include_router(patient_router, tags=["患者管理"])

