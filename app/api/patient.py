"""
病人数据和诊断相关 API 路由

工作流程说明：
=============
1. 预就诊阶段（在另一个系统完成）：
   - 患者在预就诊系统完成信息采集（身高、体重、对话等）
   - 系统生成 PreDiagnosisRecord 数据

2. 预就诊记录上传（POST /medical-record）：
   - 预就诊系统调用此接口，上传 PreDiagnosisRecord
   - 后端根据手机号查找患者，如不存在则自动创建
   - 创建 PatientMedicalRecord 和 PreDiagnosisRecord
   - **注意：此接口不需要医生认证，供其他系统模块调用**

3. 医生诊室就诊（需要医生登录认证）：
   - 医生首先登录系统（POST /doctor/login），获取JWT令牌
   - 患者使用二维码或输入手机号
   - 医生调用 GET /patient/query?phone={phone} 查询患者信息和历史就诊记录
   - 医生查看预就诊信息（PreDiagnosisRecord）
   - 医生与患者对话，ASR实时转录
   - 调用 POST /medical-record/{record_id}/ai-diagnosis 生成AI诊断建议
   - 医生调整诊断，提交最终诊断（待实现）
   - **所有医生操作都需要在请求头中携带 JWT 令牌进行认证**
"""
from fastapi import APIRouter, Depends, Request, Query, Path
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_active_doctor
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import (
    ValidationException,
    DuplicateException,
    DatabaseException,
    NotFoundException,
)
from app.core.logging import get_logger, log_request, log_response, log_error
from app.models.patient import (
    Patient,
    PatientMedicalRecord,
    PreDiagnosisRecord,
    SanzhenAnalysisResult,
    AIDiagnosisRecord,
    Doctor,
)
from app.schemas.patient import (
    QRcodeRecord,
    PatientResponse,
    PatientQueryResponse,
    MedicalRecordCreate,
    MedicalRecordResponse,
    MedicalRecordListItem,
    CompleteMedicalRecordResponse,
    AIDiagnosisCreate,
    AIDiagnosisResponse,
    APIResponse,
)
from app.services.tcm_diagnosis_service import TCMDiagnosisService

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


def get_tcm_service() -> TCMDiagnosisService:
    """获取中医诊断服务实例"""
    return TCMDiagnosisService(
        api_key=settings.AI_API_KEY,
        base_url=settings.AI_BASE_URL,
        model_name=settings.AI_MODEL_NAME
    )


@router.get("/patient/query", response_model=APIResponse, status_code=200)
async def query_patient_by_phone(
    request: Request,
    phone: str = Query(..., description="患者手机号"),
    db: AsyncSession = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_active_doctor),
):
    """
    通过手机号查询患者信息和历史就诊记录
    
    **使用场景：**
    - 医生诊室：扫描患者二维码或输入手机号后，查找患者信息和历史就诊记录
    - 前端展示：患者列表（包括首次就诊或历史就诊）
    
    - **phone**: 患者的11位手机号
    
    **认证：**
    需要医生登录认证，在请求头中提供有效的JWT令牌：
    Authorization: Bearer <access_token>
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        log_request(logger, endpoint, {"phone": phone})
        
        # 查询患者信息
        result = await db.execute(
            select(Patient).where(Patient.phone == phone)
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise NotFoundException(message=f"未找到手机号为 {phone} 的患者")
        
        # 查询患者的历史就诊记录
        medical_records_result = await db.execute(
            select(PatientMedicalRecord)
            .where(PatientMedicalRecord.patient_id == patient.patient_id)
            .order_by(PatientMedicalRecord.created_at.desc())
        )
        medical_records = medical_records_result.scalars().all()
        
        # 构建响应
        medical_records_list = [
            MedicalRecordListItem(
                record_id=record.record_id,
                uuid=record.uuid,
                status=record.status,
                created_at=record.created_at,
                patient_name=patient.name,
                patient_phone=patient.phone
            )
            for record in medical_records
        ]
        
        query_response = PatientQueryResponse(
            patient=PatientResponse.model_validate(patient),
            medical_records=medical_records_list
        )
        
        response = APIResponse(
            success=True,
            message="患者信息查询成功",
            data=query_response.model_dump()
        )
        
        log_response(logger, endpoint, {"patient_id": patient.patient_id, "records_count": len(medical_records_list)})
        
        return response
        
    except NotFoundException:
        raise
        
    except Exception as e:
        error_msg = "查询患者信息时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))


@router.post("/medical-record", response_model=APIResponse, status_code=201)
async def create_medical_record(
    request: Request,
    record_data: MedicalRecordCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建就诊记录（预就诊系统调用）
    
    **使用场景：**
    预就诊系统完成患者信息采集后，调用此接口上传预就诊数据。
    如果患者不存在（根据手机号判断），系统将自动创建患者记录。
    
    **重要说明：**
    - 此接口由预就诊系统调用，不是医生诊室使用
    - 患者信息（patient_info）仅在首次就诊时提供
    - UUID由预就诊系统生成，用于幂等性控制
    
    - **record_data**: 就诊记录信息，包含患者信息和预诊记录
    
    **认证：**
    此接口不需要医生认证，因为它是由其他系统模块调用的。
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        log_request(logger, endpoint, record_data.model_dump())
        
        # 检查患者是否存在
        result = await db.execute(
            select(Patient).where(Patient.phone == record_data.patient_phone)
        )
        patient = result.scalar_one_or_none()
        
        # 如果患者不存在且提供了患者信息，则创建新患者
        if not patient:
            if not record_data.patient_info:
                raise ValidationException(
                    message="患者不存在，请提供患者信息",
                    detail=f"手机号 {record_data.patient_phone} 未注册"
                )
            
            patient = Patient(
                name=record_data.patient_info.name,
                sex=record_data.patient_info.sex,
                birthday=record_data.patient_info.birthday,
                phone=record_data.patient_info.phone
            )
            db.add(patient)
            await db.flush()
            logger.info(f"创建新患者: patient_id={patient.patient_id}")
        
        # 检查就诊记录UUID是否已存在
        result = await db.execute(
            select(PatientMedicalRecord).where(PatientMedicalRecord.uuid == record_data.uuid)
        )
        existing_record = result.scalar_one_or_none()
        
        if existing_record:
            raise DuplicateException(message=f"就诊记录 UUID {record_data.uuid} 已存在")
        
        # 创建就诊记录
        medical_record = PatientMedicalRecord(
            patient_id=patient.patient_id,
            uuid=record_data.uuid,
            status="pending"
        )
        db.add(medical_record)
        await db.flush()
        
        # 创建预诊记录
        pre_diagnosis = PreDiagnosisRecord(
            record_id=medical_record.record_id,
            uuid=record_data.pre_diagnosis.uuid,
            height=record_data.pre_diagnosis.height,
            weight=record_data.pre_diagnosis.weight,
            coze_conversation_log=record_data.pre_diagnosis.coze_conversation_log
        )
        db.add(pre_diagnosis)
        await db.flush()
        
        # 如果有三诊分析结果，创建分析记录
        if record_data.pre_diagnosis.sanzhen_analysis:
            sanzhen = SanzhenAnalysisResult(
                pre_diagnosis_id=pre_diagnosis.pre_diagnosis_id,
                face=record_data.pre_diagnosis.sanzhen_analysis.face,
                tongue_front=record_data.pre_diagnosis.sanzhen_analysis.tongue_front,
                tongue_bottom=record_data.pre_diagnosis.sanzhen_analysis.tongue_bottom,
                pulse=record_data.pre_diagnosis.sanzhen_analysis.pulse,
                diagnosis_result=record_data.pre_diagnosis.sanzhen_analysis.diagnosis_result
            )
            db.add(sanzhen)
        
        await db.commit()
        await db.refresh(medical_record)
        
        # 加载关联数据
        await db.refresh(medical_record, ["patient", "pre_diagnosis"])
        if medical_record.pre_diagnosis:
            await db.refresh(medical_record.pre_diagnosis, ["sanzhen_result"])
        
        logger.info(f"成功创建就诊记录: record_id={medical_record.record_id}")
        
        response_data = MedicalRecordResponse.model_validate(medical_record)
        response = APIResponse(
            success=True,
            message="就诊记录创建成功",
            data=response_data.model_dump()
        )
        
        log_response(logger, endpoint, response.model_dump())
        
        return response
        
    except (DuplicateException, ValidationException):
        raise
        
    except Exception as e:
        error_msg = "创建就诊记录时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))


@router.get("/medical-record/{record_id}", response_model=APIResponse, status_code=200)
async def get_medical_record(
    request: Request,
    record_id: int = Path(..., description="就诊记录ID"),
    db: AsyncSession = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_active_doctor),
):
    """
    获取完整的就诊记录信息
    
    - **record_id**: 就诊记录ID
    
    **认证：**
    需要医生登录认证，在请求头中提供有效的JWT令牌：
    Authorization: Bearer <access_token>
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        log_request(logger, endpoint, {"record_id": record_id})
        
        # 查询就诊记录，包含所有关联数据
        result = await db.execute(
            select(PatientMedicalRecord)
            .options(
                selectinload(PatientMedicalRecord.patient),
                selectinload(PatientMedicalRecord.pre_diagnosis).selectinload(PreDiagnosisRecord.sanzhen_result),
                selectinload(PatientMedicalRecord.diagnoses)
            )
            .where(PatientMedicalRecord.record_id == record_id)
        )
        medical_record = result.scalar_one_or_none()
        
        if not medical_record:
            raise NotFoundException(message=f"未找到就诊记录 ID: {record_id}")
        
        response_data = CompleteMedicalRecordResponse.model_validate(medical_record)
        response = APIResponse(
            success=True,
            message="就诊记录查询成功",
            data=response_data.model_dump()
        )
        
        log_response(logger, endpoint, response.model_dump())
        
        return response
        
    except NotFoundException:
        raise
        
    except Exception as e:
        error_msg = "查询就诊记录时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))


@router.post("/medical-record/{record_id}/ai-diagnosis", response_model=APIResponse, status_code=201)
async def create_ai_diagnosis(
    request: Request,
    record_id: int = Path(..., description="就诊记录ID"),
    diagnosis_data: AIDiagnosisCreate = ...,
    db: AsyncSession = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_active_doctor),
):
    """
    为就诊记录生成AI诊断
    
    - **record_id**: 就诊记录ID
    - **diagnosis_data**: 包含ASR转录文本的诊断请求数据
    **认证：**
    需要医生登录认证，在请求头中提供有效的JWT令牌：
    Authorization: Bearer <access_token>
    """
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        log_request(logger, endpoint, {"record_id": record_id, "asr_text_length": len(diagnosis_data.asr_text)})
        
        # 查询就诊记录
        result = await db.execute(
            select(PatientMedicalRecord)
            .options(selectinload(PatientMedicalRecord.pre_diagnosis))
            .where(PatientMedicalRecord.record_id == record_id)
        )
        medical_record = result.scalar_one_or_none()
        
        if not medical_record:
            raise NotFoundException(message=f"未找到就诊记录 ID: {record_id}")
        
        # 获取身高体重信息,以及预问诊AI患者回答交互信息
        height = None
        weight = None
        coze_conversation_log = None
        if medical_record.pre_diagnosis:
            height = medical_record.pre_diagnosis.height
            weight = medical_record.pre_diagnosis.weight
            coze_conversation_log = medical_record.pre_diagnosis.coze_conversation_log
        
        # 调用AI诊断服务
        logger.info(f"开始为就诊记录 {record_id} 生成AI诊断...")
        tcm_service = get_tcm_service()
        
        diagnosis_result = tcm_service.process_complete_diagnosis(
            transcript=diagnosis_data.asr_text,
            height=height,
            weight=weight,
            coze_conversation_log=coze_conversation_log
        )
        
        if diagnosis_result["overall_status"] == "failed":
            raise DatabaseException(
                message="AI诊断失败",
                detail=diagnosis_result.get("error_message", "未知错误")
            )
        
        # 保存AI诊断记录
        ai_diagnosis = AIDiagnosisRecord(
            record_id=record_id,
            formatted_medical_record=diagnosis_result["medical_record_result"].get("medical_record"),
            type_inference=diagnosis_result["diagnosis_result"].get("diagnosis"),
            prescription=diagnosis_result["prescription_result"].get("prescription"),
            exercise_prescription=diagnosis_result["exercise_prescription_result"].get("exercise_prescription"),
            diagnosis_explanation=diagnosis_result["diagnosis_result"].get("diagnosis_explanation"),
            response_time=diagnosis_result.get("total_processing_time"),
            model_name=settings.AI_MODEL_NAME
        )
        
        db.add(ai_diagnosis)
        
        # 更新就诊记录状态
        medical_record.status = "completed"
        
        await db.commit()
        await db.refresh(ai_diagnosis)
        
        logger.info(f"成功创建AI诊断记录: diagnosis_id={ai_diagnosis.diagnosis_id}")
        
        response_data = AIDiagnosisResponse.model_validate(ai_diagnosis)
        response = APIResponse(
            success=True,
            message="AI诊断完成",
            data=response_data.model_dump()
        )
        
        log_response(logger, endpoint, response.model_dump())
        
        return response
        
    except NotFoundException:
        raise
        
    except Exception as e:
        error_msg = "生成AI诊断时发生错误"
        log_error(logger, error_msg, e)
        raise DatabaseException(message=error_msg, detail=str(e))


@router.post("/medical-record/{record_id}/ai-diagnosis/stream", status_code=200)
async def create_ai_diagnosis_stream(
    request: Request,
    record_id: int = Path(..., description="就诊记录ID"),
    diagnosis_data: AIDiagnosisCreate = ...,
    db: AsyncSession = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_active_doctor),
):
    """
    为就诊记录生成AI诊断（流式返回）
    
    使用 Server-Sent Events (SSE) 流式返回诊断过程，提升用户体验。
    
    - **record_id**: 就诊记录ID
    - **diagnosis_data**: 包含ASR转录文本的诊断请求数据
    
    **事件类型：**
    - `stage_start`: 阶段开始，包含 stage、stage_name、step
    - `content`: 内容流，包含 stage、chunk（实际内容片段）
    - `stage_complete`: 阶段完成，包含 stage、stage_name、result
    - `complete`: 全部完成，包含完整的诊断结果
    - `error`: 错误信息
    
    **认证：**
    需要医生登录认证，在请求头中提供有效的JWT令牌：
    Authorization: Bearer <access_token>
    """
    import json
    endpoint = f"{request.method} {request.url.path}"
    
    log_request(logger, endpoint, {"record_id": record_id, "asr_text_length": len(diagnosis_data.asr_text)})
    
    # 查询就诊记录
    result = await db.execute(
        select(PatientMedicalRecord)
        .options(selectinload(PatientMedicalRecord.pre_diagnosis))
        .where(PatientMedicalRecord.record_id == record_id)
    )
    medical_record = result.scalar_one_or_none()
    
    if not medical_record:
        raise NotFoundException(message=f"未找到就诊记录 ID: {record_id}")
    
    # 获取身高体重信息,以及预问诊AI患者回答交互信息
    height = None
    weight = None
    coze_conversation_log = None
    if medical_record.pre_diagnosis:
        height = medical_record.pre_diagnosis.height
        weight = medical_record.pre_diagnosis.weight
        coze_conversation_log = medical_record.pre_diagnosis.coze_conversation_log
    
    # 存储诊断结果用于后续保存
    diagnosis_result_holder = {"data": None}
    
    async def generate_stream():
        """生成SSE流"""
        tcm_service = get_tcm_service()
        
        try:
            async for event_data in tcm_service.stream_complete_diagnosis(
                transcript=diagnosis_data.asr_text,
                height=height,
                weight=weight,
                coze_conversation_log=coze_conversation_log
            ):
                yield event_data
                
                # 解析complete事件以获取最终结果
                if event_data.startswith("event: complete"):
                    lines = event_data.strip().split("\n")
                    for line in lines:
                        if line.startswith("data: "):
                            diagnosis_result_holder["data"] = json.loads(line[6:])
                            break
        except Exception as e:
            logger.error(f"流式诊断出错: {str(e)}")
            error_event = f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"
            yield error_event
    
    async def stream_and_save():
        """流式返回并在完成后保存结果"""
        async for event_data in generate_stream():
            yield event_data
        
        # 流结束后，保存诊断记录
        if diagnosis_result_holder["data"] and diagnosis_result_holder["data"].get("status") == "success":
            try:
                final_result = diagnosis_result_holder["data"]
                
                ai_diagnosis = AIDiagnosisRecord(
                    record_id=record_id,
                    formatted_medical_record=final_result.get("formatted_medical_record"),
                    type_inference=final_result.get("type_inference"),
                    prescription=final_result.get("prescription"),
                    exercise_prescription=final_result.get("exercise_prescription"),
                    diagnosis_explanation=final_result.get("diagnosis_explanation"),
                    response_time=final_result.get("total_processing_time"),
                    model_name=settings.AI_MODEL_NAME
                )
                
                db.add(ai_diagnosis)
                medical_record.status = "completed"
                await db.commit()
                await db.refresh(ai_diagnosis)
                
                logger.info(f"成功保存流式AI诊断记录: diagnosis_id={ai_diagnosis.diagnosis_id}")
                
                # 发送保存成功事件
                save_event = f"event: saved\ndata: {json.dumps({'diagnosis_id': ai_diagnosis.diagnosis_id, 'message': '诊断记录已保存'}, ensure_ascii=False)}\n\n"
                yield save_event
                
            except Exception as e:
                logger.error(f"保存诊断记录失败: {str(e)}")
                error_event = f"event: save_error\ndata: {json.dumps({'message': f'保存诊断记录失败: {str(e)}'}, ensure_ascii=False)}\n\n"
                yield error_event
    
    logger.info(f"开始为就诊记录 {record_id} 生成流式AI诊断...")
    
    return StreamingResponse(
        stream_and_save(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        }
    )
