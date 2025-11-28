"""
Feed Schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from app.schemas.video import VideoResponse


class FeedResponse(BaseModel):
    videos: List[VideoResponse]
    next_cursor: Optional[str] = None
    has_more: bool

