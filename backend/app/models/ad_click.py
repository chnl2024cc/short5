"""
AdClick Model - Tracks when users click on ad video links
Similar structure to ShareClick for consistency
Always uses session_id for consistent analytics tracking
"""
from sqlalchemy import Column, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class AdClick(Base):
    __tablename__ = "ad_clicks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)  # Which ad video was clicked
    clicker_session_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Who clicked (nullable for anonymous)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # Authenticated user (nullable)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # When link was clicked

    # Relationships
    video = relationship("Video", backref="ad_clicks")
    user = relationship("User", backref="ad_clicks")

    __table_args__ = (
        {"extend_existing": True},
    )

