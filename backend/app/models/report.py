"""
Report Model
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ReportType(str, enum.Enum):
    VIDEO = "video"
    USER = "user"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(SQLEnum(ReportType, native_enum=False), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # video_id or user_id
    reason = Column(Text)
    status = Column(SQLEnum(ReportStatus, native_enum=False), default=ReportStatus.PENDING, index=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], backref="reports_made")
    resolver = relationship("User", foreign_keys=[resolved_by], backref="reports_resolved")

    __table_args__ = (
        {"extend_existing": True},
    )
