"""
医生用户相关 API 路由

包含医生的注册、登录、信息查询、信息更新、密码修改等功能。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_active_doctor,
)
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import (
    ValidationException,
    DuplicateException,
    DatabaseException,
    NotFoundException,
)
from app.core.logging import get_logger, log_request, log_response, log_error
from app.models.patient import Doctor
from app.schemas.doctor import (
    DoctorRegister,
    DoctorLogin,
    DoctorResponse,
    DoctorUpdate,
    PasswordChange,
    LoginResponse,
)
from app.schemas.patient import APIResponse

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.post("/register", response_model=APIResponse, status_code=201)
async def register_doctor(
    request: Request,
    doctor_data: DoctorRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    医生注册
    
    **使用场景：**
    新医生注册账户
    
    **必填字段：**
    - username: 登录用户名（唯一）
    - password: 密码（至少6位）
    - name: 医生姓名
    - gender: 性别（MALE/FEMALE/OTHER）
    - phone: 手机号（唯一）
    
    **可选字段：**
    - department: 科室
    - position: 职位
    - bio: 个人简介
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        log_request(logger, endpoint, {
            "username": doctor_data.username,
            "name": doctor_data.name,
            "phone": doctor_data.phone
        })
        
        # 检查用户名是否已存在
        result = await db.execute(
            select(Doctor).where(Doctor.username == doctor_data.username)
        )
        if result.scalar_one_or_none():
            raise DuplicateException(message=f"用户名 {doctor_data.username} 已被注册")
        
        # 检查手机号是否已存在
        result = await db.execute(
            select(Doctor).where(Doctor.phone == doctor_data.phone)
        )
        if result.scalar_one_or_none():
            raise DuplicateException(message=f"手机号 {doctor_data.phone} 已被注册")
        
        # 创建新医生
        hashed_password = hash_password(doctor_data.password)
        doctor = Doctor(
            username=doctor_data.username,
            password_hash=hashed_password,
            name=doctor_data.name,
            gender=doctor_data.gender,
            phone=doctor_data.phone,
            department=doctor_data.department,
            position=doctor_data.position,
            bio=doctor_data.bio,
        )
        
        db.add(doctor)
        await db.commit()
        await db.refresh(doctor)
        
        logger.info(f"医生注册成功: doctor_id={doctor.doctor_id}, username={doctor.username}")
        
        response_data = DoctorResponse.model_validate(doctor)
        response = APIResponse(
            success=True,
            message="医生注册成功",
            data=response_data.model_dump()
        )
        
        log_response(logger, endpoint, {"doctor_id": doctor.doctor_id})
        
        return response
        
    except (DuplicateException, ValidationException):
        raise
        
    except Exception as e:
        error_msg = "医生注册时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))


@router.post("/login", response_model=APIResponse, status_code=200)
async def login_doctor(
    request: Request,
    login_data: DoctorLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    医生登录
    
    **使用场景：**
    医生使用用户名或手机号和密码登录系统
    
    **参数：**
    - username: 用户名或手机号
    - password: 密码
    
    **返回：**
    - access_token: JWT访问令牌
    - token_type: 令牌类型（bearer）
    - doctor: 医生信息
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        log_request(logger, endpoint, {"login_identifier": login_data.username})
        
        # 查询医生（支持用户名或手机号）
        result = await db.execute(
            select(Doctor).where(
                or_(
                    Doctor.username == login_data.username,
                    Doctor.phone == login_data.username
                )
            )
        )
        doctor = result.scalar_one_or_none()
        
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/手机号或密码错误"
            )
        
        # 验证密码
        if not verify_password(login_data.password, doctor.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/手机号或密码错误"
            )
        
        # 更新最后登录时间
        doctor.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(doctor)
        
        # 生成访问令牌
        access_token = create_access_token(
            data={
                "doctor_id": doctor.doctor_id,
                "username": doctor.username
            }
        )
        
        logger.info(f"医生登录成功: doctor_id={doctor.doctor_id}, username={doctor.username}")
        
        login_response = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            doctor=DoctorResponse.model_validate(doctor)
        )
        
        response = APIResponse(
            success=True,
            message="登录成功",
            data=login_response.model_dump()
        )
        
        log_response(logger, endpoint, {"doctor_id": doctor.doctor_id})
        
        return response
        
    except HTTPException:
        raise
        
    except Exception as e:
        error_msg = "登录时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))


@router.get("/me", response_model=APIResponse, status_code=200)
async def get_current_doctor_info(
    request: Request,
    current_doctor: Doctor = Depends(get_current_active_doctor),
):
    """
    获取当前登录医生的信息
    
    **使用场景：**
    医生查看自己的账户信息
    
    **认证：**
    需要在请求头中提供有效的JWT令牌：
    Authorization: Bearer <access_token>
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        log_request(logger, endpoint, {"doctor_id": current_doctor.doctor_id})
        
        response_data = DoctorResponse.model_validate(current_doctor)
        response = APIResponse(
            success=True,
            message="获取医生信息成功",
            data=response_data.model_dump()
        )
        
        log_response(logger, endpoint, {"doctor_id": current_doctor.doctor_id})
        
        return response
        
    except Exception as e:
        error_msg = "获取医生信息时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))


@router.put("/me", response_model=APIResponse, status_code=200)
async def update_current_doctor_info(
    request: Request,
    update_data: DoctorUpdate,
    current_doctor: Doctor = Depends(get_current_active_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    更新当前登录医生的信息
    
    **使用场景：**
    医生修改自己的账户信息
    
    **可更新字段：**
    - name: 医生姓名
    - gender: 性别
    - phone: 手机号
    - department: 科室
    - position: 职位
    - bio: 个人简介
    
    **认证：**
    需要在请求头中提供有效的JWT令牌
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        log_request(logger, endpoint, {
            "doctor_id": current_doctor.doctor_id,
            "update_data": update_data.model_dump(exclude_unset=True)
        })
        
        # 如果更新手机号，检查是否已被其他医生使用
        if update_data.phone and update_data.phone != current_doctor.phone:
            result = await db.execute(
                select(Doctor).where(
                    Doctor.phone == update_data.phone,
                    Doctor.doctor_id != current_doctor.doctor_id
                )
            )
            if result.scalar_one_or_none():
                raise DuplicateException(message=f"手机号 {update_data.phone} 已被其他医生使用")
        
        # 更新字段
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(current_doctor, field, value)
        
        current_doctor.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(current_doctor)
        
        logger.info(f"医生信息更新成功: doctor_id={current_doctor.doctor_id}")
        
        response_data = DoctorResponse.model_validate(current_doctor)
        response = APIResponse(
            success=True,
            message="医生信息更新成功",
            data=response_data.model_dump()
        )
        
        log_response(logger, endpoint, {"doctor_id": current_doctor.doctor_id})
        
        return response
        
    except (DuplicateException, ValidationException):
        raise
        
    except Exception as e:
        error_msg = "更新医生信息时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))


@router.post("/change-password", response_model=APIResponse, status_code=200)
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_doctor: Doctor = Depends(get_current_active_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    修改当前登录医生的密码
    
    **使用场景：**
    医生修改自己的登录密码
    
    **参数：**
    - old_password: 旧密码
    - new_password: 新密码（至少6位）
    
    **认证：**
    需要在请求头中提供有效的JWT令牌
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        log_request(logger, endpoint, {"doctor_id": current_doctor.doctor_id})
        
        # 验证旧密码
        if not verify_password(password_data.old_password, current_doctor.password_hash):
            raise ValidationException(message="旧密码不正确")
        
        # 更新密码
        current_doctor.password_hash = hash_password(password_data.new_password)
        current_doctor.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"医生密码修改成功: doctor_id={current_doctor.doctor_id}")
        
        response = APIResponse(
            success=True,
            message="密码修改成功",
            data=None
        )
        
        log_response(logger, endpoint, {"doctor_id": current_doctor.doctor_id})
        
        return response
        
    except ValidationException:
        raise
        
    except Exception as e:
        error_msg = "修改密码时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))

