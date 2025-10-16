"""
病人数据库模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Patient(Base):
    """病人数据模型"""
    
    __tablename__ = "patients"
    
    # 主键，使用客户端提供的 UUID
    uuid: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    
    # 必填字段
    phone: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    
    # 基本信息（可选）
    name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    birthday: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    height: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    weight: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # 四诊分析结果（可选）
    analysis_face: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analysis_tongue_front: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analysis_tongue_bottom: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analysis_pulse: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 对话记录（可选）
    coze_conversation_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Patient(uuid={self.uuid}, phone={self.phone}, name={self.name})>"

