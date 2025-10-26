"""
认证相关功能模块
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.patient import Doctor
from app.schemas.doctor import TokenData

settings = get_settings()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证
security = HTTPBearer()


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """解码访问令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        doctor_id: int = payload.get("doctor_id")
        username: str = payload.get("username")
        
        if doctor_id is None or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(doctor_id=doctor_id, username=username)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_doctor(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Doctor:
    """获取当前登录的医生"""
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    # 从数据库查询医生信息
    result = await db.execute(
        select(Doctor).where(Doctor.doctor_id == token_data.doctor_id)
    )
    doctor = result.scalar_one_or_none()
    
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="医生账户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return doctor


async def get_current_active_doctor(
    current_doctor: Doctor = Depends(get_current_doctor)
) -> Doctor:
    """获取当前活跃的医生（可以在此添加额外的验证逻辑）"""
    # 这里可以添加额外的验证，例如检查账户是否被禁用等
    return current_doctor

