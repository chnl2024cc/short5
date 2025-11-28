"""
Video Model
"""
from sqlalchemy import Column, String, Text, Integer, BigInteger, ForeignKey, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
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


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255))
    description = Column(Text)
    status = Column(Enum(VideoStatus), default=VideoStatus.UPLOADING, index=True)
    url_hls = Column(Text)
    url_mp4 = Column(Text)
    thumbnail = Column(Text)
    duration_seconds = Column(Integer)
    file_size_bytes = Column(BigInteger)
    original_filename = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="videos")

