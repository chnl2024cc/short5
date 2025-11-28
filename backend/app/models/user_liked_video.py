"""
User Liked Video Model (Saved List)
"""
from sqlalchemy import Column, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class UserLikedVideo(Base):
    __tablename__ = "user_liked_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="liked_videos")
    video = relationship("Video", backref="liked_by_users")

    __table_args__ = (
        {"extend_existing": True},
    )

