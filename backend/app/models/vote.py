"""
Vote/Swipe Model
"""
from sqlalchemy import Column, ForeignKey, DateTime, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class VoteDirection(str, enum.Enum):
    LIKE = "like"
    NOT_LIKE = "not_like"


class Vote(Base):
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(
        ENUM(VoteDirection, name="vote_direction", create_type=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="votes")
    video = relationship("Video", backref="votes")

    __table_args__ = (
        {"extend_existing": True},
    )

