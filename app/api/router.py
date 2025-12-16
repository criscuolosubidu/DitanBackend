"""API 路由汇总"""
from fastapi import APIRouter

from app.api.doctor import router as doctor_router
from app.api.patient import router as patient_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(patient_router, tags=["患者管理"])
api_v1_router.include_router(doctor_router, prefix="/doctor", tags=["医生管理"])
