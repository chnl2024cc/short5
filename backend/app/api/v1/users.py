"""
User Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String
from typing import Optional
import logging
from pydantic import ValidationError

from app.core.database import get_db
from app.api.v1.dependencies import get_current_user_required
from app.models.user import User
from app.models.video import Video
from app.models.vote import Vote
from app.models.view import View
from app.schemas.video import VideoResponse, UserBasic, VideoStats
from app.schemas.auth import UserProfileResponse, UserStats

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """
    Get current user profile with statistics.
    
    Returns user information including:
    - Basic user info (id, username, email, created_at)
    - Statistics (videos uploaded, likes received, total views)
    """
    try:
        # Get user stats - use separate queries for clarity
        # Videos count
        videos_result = await db.execute(
            select(func.count(Video.id)).where(Video.user_id == current_user.id)
        )
        videos_uploaded = videos_result.scalar() or 0
        
        # Likes received on user's videos
        # Cast direction to String to avoid enum type coercion issues
        likes_result = await db.execute(
            select(func.count(Vote.id))
            .join(Video, Vote.video_id == Video.id)
            .where(
                Video.user_id == current_user.id,
                cast(Vote.direction, String) == "like"
            )
        )
        total_likes = likes_result.scalar() or 0
        
        # Views on user's videos
        views_result = await db.execute(
            select(func.count(View.id))
            .join(Video, View.video_id == Video.id)
            .where(Video.user_id == current_user.id)
        )
        total_views = views_result.scalar() or 0
        
        # Format created_at
        created_at_str = None
        if current_user.created_at:
            if isinstance(current_user.created_at, str):
                created_at_str = current_user.created_at
            else:
                created_at_str = current_user.created_at.isoformat()
        
        # Build response - ensure all required fields are present
        # User model has NOT NULL constraints, but we'll be defensive
        username = current_user.username if current_user.username else ""
        email = current_user.email if current_user.email else ""
        
        # Create stats object
        stats = UserStats(
            videos_uploaded=int(videos_uploaded),
            total_likes_received=int(total_likes),
            total_views=int(total_views),
        )
        
        # Create and validate response
        try:
            response = UserProfileResponse(
                id=str(current_user.id),
                username=username,
                email=email,
                created_at=created_at_str,
                stats=stats,
            )
            return response
        except ValidationError as ve:
            logger.error(
                f"Pydantic validation error for user {current_user.id}: {ve.errors()}",
                exc_info=True
            )
            from app.core.config import settings
            if settings.ENVIRONMENT == "development":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Response validation error: {ve.errors()}"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user profile"
            )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_details = str(e)
        error_traceback = traceback.format_exc()
        
        logger.error(
            f"Error fetching user profile for user {current_user.id}: {error_details}\n{error_traceback}",
            exc_info=True
        )
        
        # In development, include more details
        from app.core.config import settings
        if settings.ENVIRONMENT == "development":
            detail = f"Failed to fetch user profile: {error_details}"
        else:
            detail = "Failed to fetch user profile"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


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
        .join(Video, Vote.video_id == Video.id)
        .where(Video.user_id == user.id, cast(Vote.direction, String) == "like")
    )
    total_likes = likes_received.scalar() or 0
    
    views_count = await db.execute(
        select(func.count(View.id))
        .join(Video, View.video_id == Video.id)
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
    """Get user's liked videos - videos the user has voted with direction 'like'"""
    
    # Query videos where user has voted with direction "like"
    query = (
        select(Video, User, Vote)
        .join(Vote, Video.id == Vote.video_id)
        .join(User, Video.user_id == User.id)
        .where(
            Vote.user_id == current_user.id,
            cast(Vote.direction, String) == "like"
        )
        .order_by(Vote.created_at.desc())
    )
    
    if cursor:
        # Parse cursor (ISO format datetime string)
        try:
            from datetime import datetime
            cursor_time = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            query = query.where(Vote.created_at < cursor_time)
        except Exception:
            # If cursor parsing fails, ignore it
            pass
    
    query = query.limit(min(limit, 100))
    
    result = await db.execute(query)
    rows = result.all()
    
    videos = []
    for video, user, vote in rows:
        # Get stats
        likes_count = await db.execute(
            select(func.count(Vote.id)).where(
                Vote.video_id == video.id, cast(Vote.direction, String) == "like"
            )
        )
        not_likes_count = await db.execute(
            select(func.count(Vote.id)).where(
                Vote.video_id == video.id, cast(Vote.direction, String) == "not_like"
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
                url_mp4=video.url_mp4,
                duration_seconds=video.duration_seconds,
                error_reason=video.error_reason,  # Include error reason if video failed
                user=UserBasic(id=str(user.id), username=user.username),
                stats=VideoStats(
                    likes=likes_count.scalar() or 0,
                    not_likes=not_likes_count.scalar() or 0,
                    views=views_count.scalar() or 0,
                ),
                created_at=video.created_at,
            )
        )
    
    # Use Vote.created_at for cursor (when the user liked it)
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
                Vote.video_id == video.id, cast(Vote.direction, String) == "like"
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
                url_mp4=video.url_mp4,
                duration_seconds=video.duration_seconds,
                error_reason=video.error_reason,  # Include error reason if video failed
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

