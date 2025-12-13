"""
Video Schemas
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class VideoStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    REJECTED = "rejected"


class VideoBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    ad_link: Optional[str] = Field(None, description="External ad link (admin only)")


class VideoCreate(VideoBase):
    pass


# Define these classes BEFORE VideoResponse to avoid forward reference issues
class VideoStats(BaseModel):
    likes: int = 0
    not_likes: int = 0
    views: int = 0


class UserBasic(BaseModel):
    id: str
    username: str

    class Config:
        from_attributes = True


class VideoResponse(VideoBase):
    id: str
    status: VideoStatus
    thumbnail: Optional[str] = None
    url_mp4: Optional[str] = None  # MP4 format - works in all modern browsers
    duration_seconds: Optional[int] = None
    error_reason: Optional[str] = None  # Error message if video failed
    ad_link: Optional[str] = None  # External ad link (included from VideoBase)
    user: UserBasic
    stats: VideoStats
    created_at: datetime

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    direction: str = Field(..., pattern="^(like|not_like)$")
    session_id: Optional[str] = None  # For anonymous votes


class VoteResponse(BaseModel):
    message: str
    video_id: str
    direction: str


class ViewRequest(BaseModel):
    watched_seconds: int = Field(..., ge=0)


class ViewResponse(BaseModel):
    message: str


class ShareRequest(BaseModel):
    sharer_session_id: str  # Who created the share (always required)


class ShareClickRequest(BaseModel):
    sharer_session_id: str  # Who created the original share (from ref parameter)
    clicker_session_id: str  # Who clicked the link (always required)


class ShareResponse(BaseModel):
    message: str
    video_id: str
    share_id: Optional[str] = None  # ID of the created share


class ShareClickResponse(BaseModel):
    message: str
    video_id: str


class AdClickRequest(BaseModel):
    clicker_session_id: Optional[str] = None  # Who clicked the link (optional for anonymous)


class AdClickResponse(BaseModel):
    message: str
    video_id: str