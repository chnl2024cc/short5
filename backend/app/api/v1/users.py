"""
User Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.api.v1.dependencies import get_current_user_required
from app.models.user import User
from app.models.video import Video
from app.models.vote import Vote, VoteDirection
from app.models.view import View
from app.schemas.video import VideoResponse, UserBasic, VideoStats

router = APIRouter()


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile"""
    # Get user stats
    videos_count = await db.execute(
        select(func.count(Video.id)).where(Video.user_id == current_user.id)
    )
    videos_uploaded = videos_count.scalar() or 0
    
    likes_received = await db.execute(
        select(func.count(Vote.id))
        .join(Video)
        .where(Video.user_id == current_user.id, Vote.direction == VoteDirection.LIKE)
    )
    total_likes = likes_received.scalar() or 0
    
    views_count = await db.execute(
        select(func.count(View.id))
        .join(Video)
        .where(Video.user_id == current_user.id)
    )
    total_views = views_count.scalar() or 0
    
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "stats": {
            "videos_uploaded": videos_uploaded,
            "total_likes_received": total_likes,
            "total_views": total_views,
        },
    }


@router.get("/{user_id}")
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get public user profile"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get user stats
    videos_count = await db.execute(
        select(func.count(Video.id)).where(Video.user_id == user.id)
    )
    videos_uploaded = videos_count.scalar() or 0
    
    likes_received = await db.execute(
        select(func.count(Vote.id))
        .join(Video)
        .where(Video.user_id == user.id, Vote.direction == "like")
    )
    total_likes = likes_received.scalar() or 0
    
    views_count = await db.execute(
        select(func.count(View.id))
        .join(Video)
        .where(Video.user_id == user.id)
    )
    total_views = views_count.scalar() or 0
    
    return {
        "id": str(user.id),
        "username": user.username,
        "created_at": user.created_at,
        "stats": {
            "videos_uploaded": videos_uploaded,
            "total_likes_received": total_likes,
            "total_views": total_views,
        },
    }


@router.get("/me/liked")
async def get_liked_videos(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
    cursor: Optional[str] = None,
    limit: int = 20,
):
    """Get user's liked videos (saved list)"""
    from app.models.user_liked_video import UserLikedVideo
    from sqlalchemy import and_
    
    query = (
        select(Video, User, UserLikedVideo)
        .join(UserLikedVideo, Video.id == UserLikedVideo.video_id)
        .join(User, Video.user_id == User.id)
        .where(UserLikedVideo.user_id == current_user.id)
        .order_by(UserLikedVideo.created_at.desc())
    )
    
    if cursor:
        # Parse cursor (ISO format datetime string)
        try:
            from datetime import datetime
            cursor_time = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            query = query.where(UserLikedVideo.created_at < cursor_time)
        except Exception:
            # If cursor parsing fails, ignore it
            pass
    
    query = query.limit(min(limit, 100))
    
    result = await db.execute(query)
    rows = result.all()
    
    videos = []
    for video, user, liked_video in rows:
        # Get stats
        likes_count = await db.execute(
            select(func.count(Vote.id)).where(
                Vote.video_id == video.id, Vote.direction == VoteDirection.LIKE
            )
        )
        views_count = await db.execute(
            select(func.count(View.id)).where(View.video_id == video.id)
        )
        
        videos.append(
            VideoResponse(
                id=str(video.id),
                title=video.title,
                description=video.description,
                status=video.status.value,
                thumbnail=video.thumbnail,
                url_hls=video.url_hls,
                url_mp4=video.url_mp4,
                duration_seconds=video.duration_seconds,
                user=UserBasic(id=str(user.id), username=user.username),
                stats=VideoStats(
                    likes=likes_count.scalar() or 0,
                    views=views_count.scalar() or 0,
                ),
                created_at=video.created_at,
            )
        )
    
    # Use UserLikedVideo.created_at for cursor (when the user liked it)
    next_cursor = rows[-1][2].created_at.isoformat() if rows else None
    has_more = len(rows) == limit
    
    return {
        "videos": videos,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/me/videos")
async def get_my_videos(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
    cursor: Optional[str] = None,
    limit: int = 20,
):
    """Get current user's uploaded videos"""
    query = (
        select(Video, User)
        .join(User, Video.user_id == User.id)
        .where(Video.user_id == current_user.id)
        .order_by(Video.created_at.desc())
    )
    
    if cursor:
        try:
            from datetime import datetime
            cursor_time = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            query = query.where(Video.created_at < cursor_time)
        except Exception:
            pass
    
    query = query.limit(min(limit, 100))
    
    result = await db.execute(query)
    rows = result.all()
    
    videos = []
    for video, user in rows:
        # Get stats
        likes_count = await db.execute(
            select(func.count(Vote.id)).where(
                Vote.video_id == video.id, Vote.direction == VoteDirection.LIKE
            )
        )
        views_count = await db.execute(
            select(func.count(View.id)).where(View.video_id == video.id)
        )
        
        videos.append(
            VideoResponse(
                id=str(video.id),
                title=video.title,
                description=video.description,
                status=video.status.value,
                thumbnail=video.thumbnail,
                url_hls=video.url_hls,
                url_mp4=video.url_mp4,
                duration_seconds=video.duration_seconds,
                user=UserBasic(id=str(user.id), username=user.username),
                stats=VideoStats(
                    likes=likes_count.scalar() or 0,
                    views=views_count.scalar() or 0,
                ),
                created_at=video.created_at,
            )
        )
    
    next_cursor = rows[-1][0].created_at.isoformat() if rows else None
    has_more = len(rows) == limit
    
    return {
        "videos": videos,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }

