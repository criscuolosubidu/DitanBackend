"""
病人数据上传 API 路由
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.exceptions import (
    ValidationException,
    DuplicateException,
    DatabaseException,
)
from app.core.logging import get_logger, log_request, log_response, log_error
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, APIResponse, PatientResponse


router = APIRouter()
logger = get_logger(__name__)


@router.post("/patient", response_model=APIResponse, status_code=201)
async def create_patient(
    request: Request,
    patient_data: PatientCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建病人数据
    
    - **uuid**: 客户端生成的唯一标识符（UUID v4）
    - **phone**: 患者的11位手机号（必填）
    - **name**: 患者姓名（可选）
    - **sex**: 患者性别（男/女）（可选）
    - **birthday**: 出生日期（YYYY-MM-DD）（可选）
    - **height**: 身高（cm）（可选）
    - **weight**: 体重（kg）（可选）
    - **analysisResults**: 四诊分析结果（可选）
    - **cozeConversationLog**: 对话记录（可选）
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        # 记录请求日志
        log_request(logger, endpoint, patient_data.model_dump())
        
        # 检查 UUID 是否已存在
        result = await db.execute(
            select(Patient).where(Patient.uuid == patient_data.uuid)
        )
        existing_patient = result.scalar_one_or_none()
        
        if existing_patient:
            error_msg = f"患者 UUID {patient_data.uuid} 已存在"
            log_error(logger, error_msg)
            raise DuplicateException(message=error_msg)
        
        # 创建病人记录
        patient = Patient(
            uuid=patient_data.uuid,
            phone=patient_data.phone,
            name=patient_data.name,
            sex=patient_data.sex,
            birthday=patient_data.birthday,
            height=patient_data.height,
            weight=patient_data.weight,
            analysis_face=patient_data.analysisResults.face if patient_data.analysisResults else None,
            analysis_tongue_front=patient_data.analysisResults.tongueFront if patient_data.analysisResults else None,
            analysis_tongue_bottom=patient_data.analysisResults.tongueBottom if patient_data.analysisResults else None,
            analysis_pulse=patient_data.analysisResults.pulse if patient_data.analysisResults else None,
            coze_conversation_log=patient_data.cozeConversationLog,
        )
        
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
        
        logger.info(f"成功创建患者记录: UUID={patient.uuid}, 手机号={patient.phone}")
        
        # 构建响应
        response_data = PatientResponse.model_validate(patient)
        response = APIResponse(
            success=True,
            message="患者数据上传成功",
            data=response_data
        )
        
        # 记录响应日志
        log_response(logger, endpoint, response.model_dump())
        
        return response
        
    except DuplicateException:
        raise
        
    except ValidationException:
        raise
        
    except Exception as e:
        error_msg = "创建患者记录时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))

