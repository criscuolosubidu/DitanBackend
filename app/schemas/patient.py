"""
病人数据 Pydantic 模型
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
import re


class AnalysisResults(BaseModel):
    """四诊分析结果"""
    face: Optional[str] = Field(None, description="面诊分析结果")
    tongueFront: Optional[str] = Field(None, description="舌诊（正面）分析结果")
    tongueBottom: Optional[str] = Field(None, description="舌诊（舌下）分析结果")
    pulse: Optional[str] = Field(None, description="脉诊分析结果")


class PatientCreate(BaseModel):
    """创建病人请求模型"""
    uuid: str = Field(..., description="客户端生成的唯一标识符（UUID v4）")
    phone: str = Field(..., description="患者的11位手机号")
    name: Optional[str] = Field(None, description="患者姓名")
    sex: Optional[str] = Field(None, description="患者性别（男 或 女）")
    birthday: Optional[str] = Field(None, description="出生日期，格式: YYYY-MM-DD")
    height: Optional[str] = Field(None, description="身高（cm）")
    weight: Optional[str] = Field(None, description="体重（kg）")
    analysisResults: Optional[AnalysisResults] = Field(None, description="四诊分析结果")
    cozeConversationLog: Optional[str] = Field(None, description="与数字人完整的对话记录")
    
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
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError("手机号格式不正确")
        return v
    
    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: Optional[str]) -> Optional[str]:
        """验证性别"""
        if v is not None and v not in ["男", "女"]:
            raise ValueError("性别只能是 '男' 或 '女'")
        return v
    
    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v: Optional[str]) -> Optional[str]:
        """验证出生日期格式"""
        if v is not None:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                raise ValueError("出生日期格式不正确，应为 YYYY-MM-DD")
        return v


class PatientResponse(BaseModel):
    """病人响应模型"""
    uuid: str
    phone: str
    name: Optional[str] = None
    sex: Optional[str] = None
    birthday: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    analysis_face: Optional[str] = None
    analysis_tongue_front: Optional[str] = None
    analysis_tongue_bottom: Optional[str] = None
    analysis_pulse: Optional[str] = None
    coze_conversation_log: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class APIResponse(BaseModel):
    """通用 API 响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[PatientResponse] = Field(None, description="响应数据")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="请求是否成功")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="错误详情")

