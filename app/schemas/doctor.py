"""
医生用户相关 Pydantic 模型
"""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.patient import Gender


# ========== 医生注册相关 ==========
class DoctorRegister(BaseModel):
    """医生注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    name: str = Field(..., min_length=2, max_length=50, description="医生姓名")
    gender: Gender = Field(..., description="性别")
    phone: str = Field(..., description="手机号")
    department: Optional[str] = Field(None, max_length=100, description="科室")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    bio: Optional[str] = Field(None, description="个人简介")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式：只允许字母、数字、下划线"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError("手机号格式不正确")
        return v


# ========== 医生登录相关 ==========
class DoctorLogin(BaseModel):
    """医生登录请求"""
    username: str = Field(..., description="用户名或手机号")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    doctor: "DoctorResponse" = Field(..., description="医生信息")


# ========== 医生信息相关 ==========
class DoctorResponse(BaseModel):
    """医生信息响应"""
    doctor_id: int
    username: str
    name: str
    gender: Gender
    phone: str
    department: Optional[str] = None
    position: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class DoctorUpdate(BaseModel):
    """医生信息更新请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="医生姓名")
    gender: Optional[Gender] = Field(None, description="性别")
    phone: Optional[str] = Field(None, description="手机号")
    department: Optional[str] = Field(None, max_length=100, description="科室")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    bio: Optional[str] = Field(None, description="个人简介")
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """验证手机号格式"""
        if v is not None and not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError("手机号格式不正确")
        return v


class PasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


# ========== Token相关 ==========
class TokenData(BaseModel):
    """Token载荷数据"""
    doctor_id: int
    username: str

