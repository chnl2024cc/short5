"""
Feed Endpoint with Recommendation Algorithm
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, cast, String
from typing import Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID
import logging

from app.core.database import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.models.vote import Vote, VoteDirection
from app.models.view import View
from app.schemas.feed import FeedResponse
from app.schemas.video import VideoResponse, VideoStats, UserBasic

logger = logging.getLogger(__name__)
router = APIRouter()


async def calculate_video_score(
    video: Video,
    user_id: Optional[str],
    db: AsyncSession,
) -> float:
    """
    Calculate recommendation score for a video
    Simplified MVP version: creator-based + popularity
    """
    score = 0.5  # Base score
    
    if not user_id:
        # New user: use popularity only
        likes_count = await db.execute(
            select(func.count(Vote.id)).where(
                Vote.video_id == video.id, cast(Vote.direction, String) == "like"
            )
        )
        views_count = await db.execute(
            select(func.count(View.id)).where(View.video_id == video.id)
        )
        
        likes = likes_count.scalar() or 0
        views = views_count.scalar() or 1
        
        # Popularity score
        popularity = (likes / views) * min(views, 100) / 100
        score = 0.3 + (popularity * 0.7)
        
        # Recency boost
        days_old = (datetime.now(timezone.utc) - video.created_at).days
        recency = max(0, 1.0 - (days_old / 30))
        score += recency * 0.2
        
        return score
    
    user_uuid = UUID(user_id) if user_id else None
    
    # Get user's liked creators
    if user_uuid:
        liked_creators = await db.execute(
            select(Video.user_id)
            .join(Vote, Vote.video_id == Video.id)
            .where(Vote.user_id == user_uuid, cast(Vote.direction, String) == "like")
            .distinct()
        )
        liked_creator_ids = {row[0] for row in liked_creators.all()}  # Keep as UUID
        
        # Get user's not-liked creators
        not_liked_creators = await db.execute(
            select(Video.user_id)
            .join(Vote, Vote.video_id == Video.id)
            .where(Vote.user_id == user_uuid, cast(Vote.direction, String) == "not_like")
            .distinct()
        )
        not_liked_creator_ids = {row[0] for row in not_liked_creators.all()}  # Keep as UUID
    else:
        liked_creator_ids = set()
        not_liked_creator_ids = set()
    
    # Creator-based score (40% weight)
    if video.user_id in liked_creator_ids:
        # Count likes from this creator
        creator_likes = await db.execute(
            select(func.count(Vote.id))
            .join(Video, Vote.video_id == Video.id)
            .where(
                Vote.user_id == user_uuid,
                cast(Vote.direction, String) == "like",
                Video.user_id == video.user_id,
            )
        )
        like_count = creator_likes.scalar() or 0
        creator_score = 1.0 + min(like_count / 10, 1.0)  # Boost up to 2.0
        score += creator_score * 0.4
    elif video.user_id in not_liked_creator_ids:
        score *= 0.1  # Heavy penalty
    else:
        score += 0.5 * 0.4  # Neutral
    
    # Popularity score (30% weight)
    likes_count = await db.execute(
        select(func.count(Vote.id)).where(
            Vote.video_id == video.id, cast(Vote.direction, String) == "like"
        )
    )
    views_count = await db.execute(
        select(func.count(View.id)).where(View.video_id == video.id)
    )
    
    likes = likes_count.scalar() or 0
    views = views_count.scalar() or 1
    
    popularity = (likes / views) * min(views, 100) / 100
    score += popularity * 0.3
    
    # Recency score (20% weight)
    days_old = (datetime.now(timezone.utc) - video.created_at).days
    recency = max(0, 1.0 - (days_old / 30))
    score += recency * 0.2
    
    # Diversity multiplier (prevent too many from same creator)
    # This would need to be calculated per feed, simplified here
    score *= 1.0
    
    return score


@router.get("", response_model=FeedResponse)
async def get_feed(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cursor: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """Get personalized video feed"""
    try:
        is_authenticated = current_user is not None
        logger.info(f"[FEED] Getting feed for {'authenticated' if is_authenticated else 'unauthenticated'} user")
        
        # Base query: only ready videos with MP4 files
        query = (
            select(Video, User)
            .join(User, Video.user_id == User.id)
            .where(
                Video.status == VideoStatus.READY,
                Video.url_mp4.isnot(None),
                Video.url_mp4 != ""
            )
        )
        
        # Exclude videos user has "liked" (they can see these in the "liked" page)
        # But still show videos they've "not_liked" (in case they want to see them again)
        if current_user:
            try:
                liked_videos = await db.execute(
                    select(Vote.video_id).where(
                        Vote.user_id == current_user.id,
                        cast(Vote.direction, String) == "like"
                    )
                )
                liked_video_ids = [row[0] for row in liked_videos.all()]
                if liked_video_ids:
                    query = query.where(Video.id.notin_(liked_video_ids))
                    logger.info(f"[FEED] Excluding {len(liked_video_ids)} liked videos for authenticated user")
            except Exception as e:
                # If vote table doesn't exist or has issues, continue without filtering
                logger.warning(f"[FEED] Error filtering liked videos: {e}")
                pass
        
        # Apply cursor pagination
        if cursor:
            try:
                cursor_time = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                query = query.where(Video.created_at < cursor_time)
                logger.info(f"[FEED] Applying cursor pagination: {cursor_time}")
            except Exception as e:
                logger.warning(f"[FEED] Error parsing cursor: {e}")
                pass
        
        # Get all candidates
        logger.info(f"[FEED] Executing query with limit {limit * 3}")
        result = await db.execute(query.order_by(desc(Video.created_at)).limit(limit * 3))
        candidates = result.all()
        logger.info(f"[FEED] Found {len(candidates)} candidate videos")
        
        if not candidates:
            logger.warning(f"[FEED] No candidate videos found - returning empty feed")
            return FeedResponse(videos=[], next_cursor=None, has_more=False)
        
        # Calculate scores and sort
        scored_videos = []
        user_id = str(current_user.id) if current_user else None
        logger.info(f"[FEED] Calculating scores for {len(candidates)} videos (user_id: {user_id})")
        
        scoring_errors = 0
        for video, user in candidates:
            try:
                score = await calculate_video_score(video, user_id, db)
                scored_videos.append((score, video, user))
            except Exception as e:
                # Skip videos that cause errors in scoring
                scoring_errors += 1
                logger.warning(f"[FEED] Error scoring video {video.id}: {e}")
                continue
        
        logger.info(f"[FEED] Successfully scored {len(scored_videos)} videos ({scoring_errors} errors)")
        
        if not scored_videos:
            logger.warning(f"[FEED] No videos after scoring - returning empty feed")
            return FeedResponse(videos=[], next_cursor=None, has_more=False)
        
        # Sort by score (descending)
        scored_videos.sort(key=lambda x: x[0], reverse=True)
        
        # Take top N
        top_videos = scored_videos[:limit]
        
        # Build response
        videos = []
        for score, video, user in top_videos:
            try:
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
                        user=UserBasic(id=str(user.id), username=user.username),
                        stats=VideoStats(
                            likes=likes_count.scalar() or 0,
                            views=views_count.scalar() or 0,
                        ),
                        created_at=video.created_at,
                    )
                )
            except Exception as e:
                # Skip videos that cause errors in response building
                continue
        
        # Determine next cursor
        next_cursor = None
        has_more = len(candidates) > limit
        
        if has_more and videos:
            last_video = videos[-1]
            next_cursor = last_video.created_at.isoformat()
        
        return FeedResponse(
            videos=videos,
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except Exception as e:
        # Log the error and return empty feed
        logger.error(f"[FEED] Error in get_feed: {str(e)}", exc_info=True)
        return FeedResponse(videos=[], next_cursor=None, has_more=False)

