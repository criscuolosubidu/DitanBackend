"""医生用户相关 API 路由"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_

from app.api.deps import RequestContext, get_request_context, get_auth_context
from app.core import hash_password, verify_password, create_access_token
from app.core.exceptions import ValidationException, DuplicateException, DatabaseException
from app.models import Doctor
from app.schemas import APIResponse
from app.schemas.doctor import (
    DoctorRegister,
    DoctorLogin,
    DoctorResponse,
    DoctorUpdate,
    PasswordChange,
    LoginResponse,
)

router = APIRouter()


@router.post("/register", response_model=APIResponse, status_code=201)
async def register_doctor(
    doctor_data: DoctorRegister,
    ctx: RequestContext = Depends(get_request_context),
):
    """医生注册"""
    try:
        ctx.log_info(f"注册请求: username={doctor_data.username}")

        result = await ctx.db.execute(select(Doctor).where(Doctor.username == doctor_data.username))
        if result.scalar_one_or_none():
            raise DuplicateException(f"用户名 {doctor_data.username} 已被注册")

        result = await ctx.db.execute(select(Doctor).where(Doctor.phone == doctor_data.phone))
        if result.scalar_one_or_none():
            raise DuplicateException(f"手机号 {doctor_data.phone} 已被注册")

        doctor = Doctor(
            username=doctor_data.username,
            password_hash=hash_password(doctor_data.password),
            name=doctor_data.name,
            gender=doctor_data.gender,
            phone=doctor_data.phone,
            department=doctor_data.department,
            position=doctor_data.position,
            bio=doctor_data.bio,
        )

        ctx.db.add(doctor)
        await ctx.db.commit()
        await ctx.db.refresh(doctor)

        ctx.log_info(f"注册成功: doctor_id={doctor.doctor_id}")
        return APIResponse(
            success=True,
            message="医生注册成功",
            data=DoctorResponse.model_validate(doctor).model_dump(),
        )

    except (DuplicateException, ValidationException):
        raise
    except Exception as e:
        ctx.log_error("注册失败", e)
        raise DatabaseException("医生注册时发生错误", str(e))


@router.post("/login", response_model=APIResponse, status_code=200)
async def login_doctor(
    login_data: DoctorLogin,
    ctx: RequestContext = Depends(get_request_context),
):
    """医生登录"""
    try:
        ctx.log_info(f"登录请求: {login_data.username}")

        result = await ctx.db.execute(
            select(Doctor).where(
                or_(Doctor.username == login_data.username, Doctor.phone == login_data.username)
            )
        )
        doctor = result.scalar_one_or_none()

        if not doctor or not verify_password(login_data.password, doctor.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/手机号或密码错误",
            )

        doctor.last_login = datetime.utcnow()
        await ctx.db.commit()
        await ctx.db.refresh(doctor)

        access_token = create_access_token(
            data={"doctor_id": doctor.doctor_id, "username": doctor.username}
        )

        ctx.log_info(f"登录成功: doctor_id={doctor.doctor_id}")
        return APIResponse(
            success=True,
            message="登录成功",
            data=LoginResponse(
                access_token=access_token,
                token_type="bearer",
                doctor=DoctorResponse.model_validate(doctor),
            ).model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        ctx.log_error("登录失败", e)
        raise DatabaseException("登录时发生错误", str(e))


@router.get("/me", response_model=APIResponse, status_code=200)
async def get_current_doctor_info(ctx: RequestContext = Depends(get_auth_context)):
    """获取当前登录医生的信息"""
    try:
        ctx.log_info(f"查询信息: doctor_id={ctx.doctor.doctor_id}")
        return APIResponse(
            success=True,
            message="获取医生信息成功",
            data=DoctorResponse.model_validate(ctx.doctor).model_dump(),
        )
    except Exception as e:
        ctx.log_error("获取医生信息失败", e)
        raise DatabaseException("获取医生信息时发生错误", str(e))


@router.put("/me", response_model=APIResponse, status_code=200)
async def update_current_doctor_info(
    update_data: DoctorUpdate,
    ctx: RequestContext = Depends(get_auth_context),
):
    """更新当前登录医生的信息"""
    try:
        ctx.log_info(f"更新信息: doctor_id={ctx.doctor.doctor_id}")

        if update_data.phone and update_data.phone != ctx.doctor.phone:
            result = await ctx.db.execute(
                select(Doctor).where(
                    Doctor.phone == update_data.phone,
                    Doctor.doctor_id != ctx.doctor.doctor_id,
                )
            )
            if result.scalar_one_or_none():
                raise DuplicateException(f"手机号 {update_data.phone} 已被其他医生使用")

        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(ctx.doctor, field, value)

        ctx.doctor.updated_at = datetime.utcnow()
        await ctx.db.commit()
        await ctx.db.refresh(ctx.doctor)

        ctx.log_info(f"更新成功: doctor_id={ctx.doctor.doctor_id}")
        return APIResponse(
            success=True,
            message="医生信息更新成功",
            data=DoctorResponse.model_validate(ctx.doctor).model_dump(),
        )

    except (DuplicateException, ValidationException):
        raise
    except Exception as e:
        ctx.log_error("更新医生信息失败", e)
        raise DatabaseException("更新医生信息时发生错误", str(e))


@router.post("/change-password", response_model=APIResponse, status_code=200)
async def change_password(
    password_data: PasswordChange,
    ctx: RequestContext = Depends(get_auth_context),
):
    """修改当前登录医生的密码"""
    try:
        ctx.log_info(f"修改密码: doctor_id={ctx.doctor.doctor_id}")

        if not verify_password(password_data.old_password, ctx.doctor.password_hash):
            raise ValidationException("旧密码不正确")

        ctx.doctor.password_hash = hash_password(password_data.new_password)
        ctx.doctor.updated_at = datetime.utcnow()
        await ctx.db.commit()

        ctx.log_info(f"密码修改成功: doctor_id={ctx.doctor.doctor_id}")
        return APIResponse(success=True, message="密码修改成功", data=None)

    except ValidationException:
        raise
    except Exception as e:
        ctx.log_error("修改密码失败", e)
        raise DatabaseException("修改密码时发生错误", str(e))
