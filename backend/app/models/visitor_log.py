"""
Visitor Log Model (MVP - Minimal Implementation)
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class VisitorLog(Base):
    __tablename__ = "visitor_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Session/User
    session_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Request (Core)
    url = Column(Text, nullable=False)
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Geographic (Core)
    country = Column(String(2))
    country_name = Column(String(100))
    city = Column(String(100))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    
    # Timestamps
    visited_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="visitor_logs")

