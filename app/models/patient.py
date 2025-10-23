"""
病人相关数据库模型
"""
from datetime import datetime, date
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Text, DateTime, Date, Float, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Gender(PyEnum):
    """性别枚举"""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class DiagnosisType(PyEnum):
    """诊断类型枚举"""
    AI_DIAGNOSIS = "AI_DIAGNOSIS"
    DOCTOR_DIAGNOSIS = "DOCTOR_DIAGNOSIS"


class Patient(Base):
    """患者基本信息"""
    
    __tablename__ = "patients"
    
    patient_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sex: Mapped[Gender] = mapped_column(Enum(Gender), nullable=False)
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    phone: Mapped[str] = mapped_column(String(11), nullable=False, index=True, unique=True)
    
    # 关系
    medical_records: Mapped[List["PatientMedicalRecord"]] = relationship(
        "PatientMedicalRecord",
        back_populates="patient",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Patient(patient_id={self.patient_id}, name={self.name}, phone={self.phone})>"


class PatientMedicalRecord(Base):
    """就诊记录（聚合根）"""
    
    __tablename__ = "patient_medical_records"
    
    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.patient_id"), nullable=False, index=True)
    uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, in_progress, completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    patient: Mapped["Patient"] = relationship("Patient", back_populates="medical_records")
    pre_diagnosis: Mapped[Optional["PreDiagnosisRecord"]] = relationship(
        "PreDiagnosisRecord",
        back_populates="medical_record",
        uselist=False,
        cascade="all, delete-orphan"
    )
    diagnoses: Mapped[List["DiagnosisRecord"]] = relationship(
        "DiagnosisRecord",
        back_populates="medical_record",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<PatientMedicalRecord(record_id={self.record_id}, uuid={self.uuid}, status={self.status})>"


class PreDiagnosisRecord(Base):
    """预诊记录"""
    
    __tablename__ = "pre_diagnosis_records"
    
    pre_diagnosis_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(Integer, ForeignKey("patient_medical_records.record_id"), nullable=False, unique=True, index=True)
    uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    coze_conversation_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    medical_record: Mapped["PatientMedicalRecord"] = relationship("PatientMedicalRecord", back_populates="pre_diagnosis")
    sanzhen_result: Mapped[Optional["SanzhenAnalysisResult"]] = relationship(
        "SanzhenAnalysisResult",
        back_populates="pre_diagnosis",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<PreDiagnosisRecord(pre_diagnosis_id={self.pre_diagnosis_id}, uuid={self.uuid})>"


class SanzhenAnalysisResult(Base):
    """三诊分析结果"""
    
    __tablename__ = "sanzhen_analysis_results"
    
    sanzhen_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pre_diagnosis_id: Mapped[int] = mapped_column(Integer, ForeignKey("pre_diagnosis_records.pre_diagnosis_id"), nullable=False, unique=True, index=True)
    face: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tongue_front: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tongue_bottom: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pulse: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diagnosis_result: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # 综合诊断结果
    
    # 关系
    pre_diagnosis: Mapped["PreDiagnosisRecord"] = relationship("PreDiagnosisRecord", back_populates="sanzhen_result")
    
    def __repr__(self) -> str:
        return f"<SanzhenAnalysisResult(sanzhen_id={self.sanzhen_id}, diagnosis_result={self.diagnosis_result})>"


class DiagnosisRecord(Base):
    """诊断记录（基类）"""
    
    __tablename__ = "diagnosis_records"
    
    diagnosis_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(Integer, ForeignKey("patient_medical_records.record_id"), nullable=False, index=True)
    type: Mapped[DiagnosisType] = mapped_column(Enum(DiagnosisType), nullable=False)
    formatted_medical_record: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type_inference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 证型推断
    treatment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 治疗建议
    prescription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 处方
    exercise_prescription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 运动处方
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 多态标识
    __mapper_args__ = {
        "polymorphic_identity": "diagnosis_record",
        "polymorphic_on": "type"
    }
    
    # 关系
    medical_record: Mapped["PatientMedicalRecord"] = relationship("PatientMedicalRecord", back_populates="diagnoses")
    
    def __repr__(self) -> str:
        return f"<DiagnosisRecord(diagnosis_id={self.diagnosis_id}, type={self.type})>"


class AIDiagnosisRecord(DiagnosisRecord):
    """AI诊断记录"""
    
    __tablename__ = "ai_diagnosis_records"
    
    diagnosis_id: Mapped[int] = mapped_column(Integer, ForeignKey("diagnosis_records.diagnosis_id"), primary_key=True)
    diagnosis_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 诊断解释
    response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 响应时间（秒）
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 模型名称
    
    __mapper_args__ = {
        "polymorphic_identity": DiagnosisType.AI_DIAGNOSIS
    }
    
    def __repr__(self) -> str:
        return f"<AIDiagnosisRecord(diagnosis_id={self.diagnosis_id}, model_name={self.model_name})>"


class DoctorDiagnosisRecord(DiagnosisRecord):
    """医生诊断记录"""
    
    __tablename__ = "doctor_diagnosis_records"
    
    diagnosis_id: Mapped[int] = mapped_column(Integer, ForeignKey("diagnosis_records.diagnosis_id"), primary_key=True)
    doctor_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 医生ID
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 医生备注
    
    __mapper_args__ = {
        "polymorphic_identity": DiagnosisType.DOCTOR_DIAGNOSIS
    }
    
    def __repr__(self) -> str:
        return f"<DoctorDiagnosisRecord(diagnosis_id={self.diagnosis_id}, doctor_id={self.doctor_id})>"
