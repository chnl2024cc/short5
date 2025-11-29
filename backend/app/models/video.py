"""
Video Model
"""
from sqlalchemy import Column, String, Text, Integer, BigInteger, ForeignKey, DateTime, func, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class VideoStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    REJECTED = "rejected"


class VideoStatusType(TypeDecorator):
    """Custom type that ensures enum values (not names) are used with PostgreSQL enum"""
    impl = PG_ENUM
    cache_ok = True
    
    def __init__(self):
        super().__init__(
            'uploading', 'processing', 'ready', 'failed', 'rejected',
            name='video_status',
            create_type=False
        )
    
    def process_bind_param(self, value, dialect):
        """Convert enum to its value (string) before binding"""
        if value is None:
            return None
        if isinstance(value, VideoStatus):
            return value.value
        return value
    
    def process_result_value(self, value, dialect):
        """Convert database value back to enum"""
        if value is None:
            return None
        return VideoStatus(value)


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255))
    description = Column(Text)
    status = Column(VideoStatusType(), default=VideoStatus.UPLOADING, index=True)
    url_hls = Column(Text)
    url_mp4 = Column(Text)
    thumbnail = Column(Text)
    duration_seconds = Column(Integer)
    file_size_bytes = Column(BigInteger)
    original_filename = Column(String(255))
    error_reason = Column(Text)  # Store error message for failed videos
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="videos")

