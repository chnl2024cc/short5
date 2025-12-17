"""
Feed Endpoint - Simple Video Feed
"""
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, cast, String
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.models.vote import Vote
from app.models.view import View
from app.schemas.feed import FeedResponse
from app.schemas.video import VideoResponse, VideoStats, UserBasic

logger = logging.getLogger(__name__)
router = APIRouter()


def calculate_video_score(
    video: Video,
    likes: int,
    views: int,
) -> float:
    """
    Calculate recommendation score for a video
    Simple version: popularity + recency only
    Uses pre-fetched stats to avoid queries
    """
    # Popularity score (70% weight)
    popularity = (likes / views) * min(views, 100) / 100 if views > 0 else 0
    score = 0.3 + (popularity * 0.7)
    
    # Recency score (30% weight)
    days_old = (datetime.now(timezone.utc) - video.created_at).days
    recency = max(0, 1.0 - (days_old / 30))
    score += recency * 0.3
    
    return score


@router.get("", response_model=FeedResponse)
async def get_feed(
    response: Response,
    db: AsyncSession = Depends(get_db),
    session_id: Optional[str] = Query(None, description="Session ID to filter out voted videos"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination (ISO 8601 datetime)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of videos to return"),
):
    """Get simple video feed - shows videos not voted on by the current session"""
    # Explicitly disable caching - always return fresh data
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    try:
        logger.info(f"[FEED] Getting feed (session_id: {session_id}, limit: {limit})")
        
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
        
        # Exclude videos that have been voted on (like or not_like) by this session
        if session_id:
            try:
                session_uuid = UUID(session_id)
                voted_videos = await db.execute(
                    select(Vote.video_id).where(
                        Vote.session_id == session_uuid
                    )
                )
                voted_video_ids = [row[0] for row in voted_videos.all()]
                if voted_video_ids:
                    query = query.where(Video.id.notin_(voted_video_ids))
                    logger.info(f"[FEED] Excluding {len(voted_video_ids)} voted videos for session {session_id}")
            except (ValueError, Exception) as e:
                logger.warning(f"[FEED] Error filtering voted videos: {e}")
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
        
        # Get all candidates (3x oversampling for scoring)
        logger.info(f"[FEED] Executing query with limit {limit * 3}")
        result = await db.execute(query.order_by(desc(Video.created_at)).limit(limit * 3))
        candidates = result.all()
        logger.info(f"[FEED] Found {len(candidates)} candidate videos")
        
        if not candidates:
            logger.warning(f"[FEED] No candidate videos found - returning empty feed")
            return FeedResponse(videos=[], next_cursor=None, has_more=False)
        
        # Extract video IDs for batch querying
        candidate_video_ids = [video.id for video, user in candidates]
        
        # Batch fetch all likes counts in one query
        logger.info(f"[FEED] Batch fetching likes for {len(candidate_video_ids)} videos")
        likes_result = await db.execute(
            select(Vote.video_id, func.count(Vote.id).label('likes'))
            .where(
                Vote.video_id.in_(candidate_video_ids),
                cast(Vote.direction, String) == "like"
            )
            .group_by(Vote.video_id)
        )
        likes_map = {row[0]: row[1] for row in likes_result.all()}
        
        # Batch fetch all views counts in one query
        logger.info(f"[FEED] Batch fetching views for {len(candidate_video_ids)} videos")
        views_result = await db.execute(
            select(View.video_id, func.count(View.id).label('views'))
            .where(View.video_id.in_(candidate_video_ids))
            .group_by(View.video_id)
        )
        views_map = {row[0]: row[1] for row in views_result.all()}
        
        # Calculate scores and sort
        scored_videos = []
        logger.info(f"[FEED] Calculating scores for {len(candidates)} videos")
        
        for video, user in candidates:
            try:
                likes = likes_map.get(video.id, 0)
                views = views_map.get(video.id, 0)
                score = calculate_video_score(video, likes, views)
                scored_videos.append((score, video, user, likes, views))
            except Exception as e:
                logger.warning(f"[FEED] Error scoring video {video.id}: {e}")
                continue
        
        logger.info(f"[FEED] Successfully scored {len(scored_videos)} videos")
        
        if not scored_videos:
            logger.warning(f"[FEED] No videos after scoring - returning empty feed")
            return FeedResponse(videos=[], next_cursor=None, has_more=False)
        
        # Sort by score (descending)
        scored_videos.sort(key=lambda x: x[0], reverse=True)
        
        # Take top N
        top_videos = scored_videos[:limit]
        
        # Build response using pre-fetched stats (no caching - fresh data every time)
        videos = []
        for score, video, user, likes, views in top_videos:
            try:
                videos.append(
                    VideoResponse(
                        id=str(video.id),
                        title=video.title,
                        description=video.description,
                        status=video.status.value,
                        thumbnail=video.thumbnail,
                        url_mp4=video.url_mp4,
                        duration_seconds=video.duration_seconds,
                        error_reason=video.error_reason,
                        ad_link=video.ad_link,
                        user=UserBasic(id=str(user.id), username=user.username),
                        stats=VideoStats(
                            likes=likes,
                            views=views,
                        ),
                        created_at=video.created_at,
                    )
                )
            except Exception as e:
                logger.warning(f"[FEED] Error building response for video {video.id}: {e}")
                continue
        
        # Determine next cursor and has_more
        # Always check if there are more videos available, regardless of how many we returned.
        # This is important because we might have filtered out many videos (voted on, missing url_mp4),
        # but there could still be more videos in the database.
        next_cursor = None
        has_more = False
        
        if videos:
            last_video = videos[-1]
            
            # Always check if there are more videos available beyond the cursor
            # This ensures we continue loading even if we got fewer videos than requested
            # (which can happen if many videos were filtered out)
            check_more_query = (
                select(Video.id)
                .where(
                    Video.status == VideoStatus.READY,
                    Video.url_mp4.isnot(None),
                    Video.url_mp4 != "",
                    Video.created_at < last_video.created_at
                )
            )
            
            # Apply same filters as main query (session-based exclusion)
            if session_id:
                try:
                    session_uuid = UUID(session_id)
                    voted_videos = await db.execute(
                        select(Vote.video_id).where(
                            Vote.session_id == session_uuid
                        )
                    )
                    voted_video_ids = [row[0] for row in voted_videos.all()]
                    if voted_video_ids:
                        check_more_query = check_more_query.where(Video.id.notin_(voted_video_ids))
                except (ValueError, Exception):
                    pass
            
            # Check if there's at least one more video available
            more_result = await db.execute(check_more_query.limit(1))
            has_more = more_result.first() is not None
            
            if has_more:
                next_cursor = last_video.created_at.isoformat()
            else:
                logger.info(f"[FEED] No more videos available for session {session_id} after cursor {last_video.created_at}")
        
        return FeedResponse(
            videos=videos,
            next_cursor=next_cursor,
            has_more=has_more,
        )
    except Exception as e:
        logger.error(f"[FEED] Error in get_feed: {str(e)}", exc_info=True)
        return FeedResponse(videos=[], next_cursor=None, has_more=False)

