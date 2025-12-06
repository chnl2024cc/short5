"""
ShareLink Model - Tracks when users create share links
Separate from ShareClick to track share creation vs clicks
Always uses session_id for consistent analytics tracking
"""
from sqlalchemy import Column, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sharer_session_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Who created the share link
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # When share link was created

    # Relationships
    video = relationship("Video", backref="share_links")

    __table_args__ = (
        {"extend_existing": True},
    )

