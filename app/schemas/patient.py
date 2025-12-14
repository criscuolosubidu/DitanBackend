"""
病人数据 Pydantic 模型
"""
import re
from datetime import datetime, date
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


# 枚举类型
class Gender(str, Enum):
    """性别枚举"""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class DiagnosisType(str, Enum):
    """诊断类型枚举"""
    AI_DIAGNOSIS = "AI_DIAGNOSIS"
    DOCTOR_DIAGNOSIS = "DOCTOR_DIAGNOSIS"


# ========== QRcode相关 ==========
class QRcodeRecord(BaseModel):
    """二维码记录"""
    card_number: str = Field(..., description="卡号")
    name: str = Field(..., description="患者姓名")
    phone: str = Field(..., description="手机号")
    gender: Gender = Field(..., description="性别")
    birthday: date = Field(..., description="出生日期")
    target_weight: Optional[str] = Field(None, description="目标体重")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError("手机号格式不正确")
        return v


# ========== 患者相关 ==========
class PatientCreate(BaseModel):
    """创建患者请求"""
    name: str = Field(..., description="患者姓名")
    sex: Gender = Field(..., description="性别")
    birthday: date = Field(..., description="出生日期")
    phone: str = Field(..., description="手机号")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError("手机号格式不正确")
        return v


class PatientResponse(BaseModel):
    """患者响应"""
    patient_id: int
    name: str
    sex: Gender
    birthday: date
    phone: str

    model_config = {"from_attributes": True}


# ========== 三诊分析结果相关 ==========
class SanzhenAnalysisCreate(BaseModel):
    """三诊分析结果创建"""
    face: Optional[str] = Field(None, description="面诊结果")
    tongue_front: Optional[str] = Field(None, description="舌诊正面结果")
    tongue_bottom: Optional[str] = Field(None, description="舌诊舌下结果")
    pulse: Optional[str] = Field(None, description="脉诊结果")
    diagnosis_result: Optional[str] = Field(None, description="综合诊断结果")


class SanzhenAnalysisResponse(BaseModel):
    """三诊分析结果响应"""
    sanzhen_id: int
    face: Optional[str] = None
    tongue_front: Optional[str] = None
    tongue_bottom: Optional[str] = None
    pulse: Optional[str] = None
    diagnosis_result: Optional[str] = None

    model_config = {"from_attributes": True}


# ========== 预诊记录相关 ==========
class PreDiagnosisCreate(BaseModel):
    """创建预诊记录请求"""
    uuid: str = Field(..., description="预诊记录UUID")
    height: Optional[float] = Field(None, description="身高(cm)")
    weight: Optional[float] = Field(None, description="体重(kg)")
    coze_conversation_log: Optional[str] = Field(None, description="对话记录")
    sanzhen_analysis: Optional[SanzhenAnalysisCreate] = Field(None, description="三诊分析结果")

    @field_validator("uuid")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """验证 UUID 格式"""
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if not uuid_pattern.match(v):
            raise ValueError("UUID 格式不正确")
        return v


class PreDiagnosisResponse(BaseModel):
    """预诊记录响应"""
    pre_diagnosis_id: int
    record_id: int
    uuid: str
    height: Optional[float] = None
    weight: Optional[float] = None
    coze_conversation_log: Optional[str] = None
    sanzhen_result: Optional[SanzhenAnalysisResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ========== 就诊记录相关 ==========
class MedicalRecordCreate(BaseModel):
    """创建就诊记录请求"""
    uuid: str = Field(..., description="就诊记录UUID")
    patient_phone: str = Field(..., description="患者手机号")
    patient_info: Optional[PatientCreate] = Field(None, description="患者信息（如果是新患者）")
    pre_diagnosis: PreDiagnosisCreate = Field(..., description="预诊记录")

    @field_validator("uuid")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """验证 UUID 格式"""
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if not uuid_pattern.match(v):
            raise ValueError("UUID 格式不正确")
        return v

    @field_validator("patient_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError("手机号格式不正确")
        return v


class MedicalRecordResponse(BaseModel):
    """就诊记录响应"""
    record_id: int
    patient_id: int
    uuid: str
    status: str
    created_at: datetime
    updated_at: datetime
    patient: PatientResponse
    pre_diagnosis: Optional[PreDiagnosisResponse] = None

    model_config = {"from_attributes": True}


class MedicalRecordListItem(BaseModel):
    """就诊记录列表项"""
    record_id: int
    uuid: str
    status: str
    created_at: datetime
    patient_name: str
    patient_phone: str

    model_config = {"from_attributes": True}


# ========== 诊断记录相关 ==========
class DiagnosisRecordBase(BaseModel):
    """诊断记录基类"""
    formatted_medical_record: Optional[str] = Field(None, description="格式化病历")
    type_inference: Optional[str] = Field(None, description="证型推断")
    treatment: Optional[str] = Field(None, description="治疗建议")
    prescription: Optional[str] = Field(None, description="处方")
    exercise_prescription: Optional[str] = Field(None, description="运动处方")


class AIDiagnosisCreate(DiagnosisRecordBase):
    """创建AI诊断请求"""
    asr_text: str = Field(..., description="ASR转录文本")


class AIDiagnosisResponse(DiagnosisRecordBase):
    """AI诊断响应"""
    diagnosis_id: int
    record_id: int
    type: DiagnosisType
    diagnosis_explanation: Optional[str] = None
    response_time: Optional[float] = None
    model_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DoctorDiagnosisCreate(BaseModel):
    """创建医生诊断请求
    
    用于医生在AI诊断基础上创建自己的诊断记录。
    如果提供了 based_on_ai_diagnosis_id，则会先复制AI诊断内容，再用提供的字段覆盖。
    """
    based_on_ai_diagnosis_id: Optional[int] = Field(None, description="基于哪个AI诊断创建（可选，会复制AI诊断内容）")
    formatted_medical_record: Optional[str] = Field(None, description="格式化病历")
    type_inference: Optional[str] = Field(None, description="证型推断")
    treatment: Optional[str] = Field(None, description="治疗建议")
    prescription: Optional[str] = Field(None, description="处方")
    exercise_prescription: Optional[str] = Field(None, description="运动处方")
    comments: Optional[str] = Field(None, description="医生备注")


class DoctorDiagnosisUpdate(BaseModel):
    """更新医生诊断请求
    
    用于医生修改自己创建的诊断记录。只有提供的字段会被更新。
    """
    formatted_medical_record: Optional[str] = Field(None, description="格式化病历")
    type_inference: Optional[str] = Field(None, description="证型推断")
    treatment: Optional[str] = Field(None, description="治疗建议")
    prescription: Optional[str] = Field(None, description="处方")
    exercise_prescription: Optional[str] = Field(None, description="运动处方")
    comments: Optional[str] = Field(None, description="医生备注")


class DoctorDiagnosisResponse(DiagnosisRecordBase):
    """医生诊断响应"""
    diagnosis_id: int
    record_id: int
    type: DiagnosisType
    doctor_id: int
    doctor_name: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ========== 完整的就诊信息 ==========
class CompleteMedicalRecordResponse(BaseModel):
    """完整的就诊信息响应"""
    record_id: int
    uuid: str
    status: str
    created_at: datetime
    updated_at: datetime
    patient: PatientResponse
    pre_diagnosis: Optional[PreDiagnosisResponse] = None
    diagnoses: List[AIDiagnosisResponse | DoctorDiagnosisResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ========== 通用响应 ==========
class APIResponse(BaseModel):
    """通用 API 响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="请求是否成功")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="错误详情")


# ========== 患者查询相关 ==========
class PatientQueryResponse(BaseModel):
    """患者查询响应"""
    patient: PatientResponse
    medical_records: List[MedicalRecordListItem] = Field(default_factory=list, description="历史就诊记录")

    model_config = {"from_attributes": True}
