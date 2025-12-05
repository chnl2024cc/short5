"""
Report Model
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func, TypeDecorator
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM
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


class ReportTypeType(TypeDecorator):
    """Custom type that ensures enum values (not names) are used with PostgreSQL enum"""
    impl = PG_ENUM
    cache_ok = True
    
    def __init__(self):
        super().__init__(
            'video', 'user',
            name='report_type',
            create_type=True
        )
    
    def process_bind_param(self, value, dialect):
        """Convert enum to its value (string) before binding"""
        if value is None:
            return None
        if isinstance(value, ReportType):
            return value.value
        return value
    
    def process_result_value(self, value, dialect):
        """Convert database value back to enum"""
        if value is None:
            return None
        return ReportType(value)


class ReportStatusType(TypeDecorator):
    """Custom type that ensures enum values (not names) are used with PostgreSQL enum"""
    impl = PG_ENUM
    cache_ok = True
    
    def __init__(self):
        super().__init__(
            'pending', 'resolved', 'dismissed',
            name='report_status',
            create_type=True
        )
    
    def process_bind_param(self, value, dialect):
        """Convert enum to its value (string) before binding"""
        if value is None:
            return None
        if isinstance(value, ReportStatus):
            return value.value
        return value
    
    def process_result_value(self, value, dialect):
        """Convert database value back to enum"""
        if value is None:
            return None
        return ReportStatus(value)


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(ReportTypeType(), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # video_id or user_id
    reason = Column(Text)
    status = Column(ReportStatusType(), default=ReportStatus.PENDING, index=True)
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
