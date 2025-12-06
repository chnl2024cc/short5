"""
ShareClick Model - Tracks when users click on shared links
Separate from ShareLink model to allow tracking multiple clicks per share link
Always uses session_id for consistent analytics tracking
"""
from sqlalchemy import Column, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class ShareClick(Base):
    __tablename__ = "share_clicks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    share_link_id = Column(UUID(as_uuid=True), ForeignKey("share_links.id", ondelete="CASCADE"), nullable=False, index=True)  # Which share link was clicked
    clicker_session_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Who clicked the link
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)  # For easier querying
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # When link was clicked

    # Relationships
    share_link = relationship("ShareLink", backref="clicks")
    video = relationship("Video", backref="share_clicks")

    __table_args__ = (
        {"extend_existing": True},
    )

