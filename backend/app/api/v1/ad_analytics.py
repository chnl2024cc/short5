"""
Ad Analytics Endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import func as sql_func

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin_user
from app.models.user import User
from app.models.video import Video
from app.models.view import View
from app.models.ad_click import AdClick

router = APIRouter()


@router.get("/analytics")
async def get_ad_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    period: str = Query("week", description="Group by 'day' or 'week'"),
    days: int = Query(30, description="Number of days to look back"),
    video_id: Optional[str] = Query(None, description="Filter by specific video ID"),
):
    """Get comprehensive ad video analytics
    
    Returns:
    - Total ad clicks
    - Total ad video views
    - Click-through rate (CTR)
    - Unique clickers
    - Average clicks per ad video
    - Clicks over time
    - Top performing ad videos
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Base query filters - only videos with ad_link
    ad_video_filter = Video.ad_link.isnot(None)
    click_filters = [AdClick.clicked_at >= start_date]
    view_filters = [View.created_at >= start_date]  # Assuming views have created_at
    
    if video_id:
        click_filters.append(AdClick.video_id == video_id)
        view_filters.append(View.video_id == video_id)
        ad_video_filter = ad_video_filter & (Video.id == video_id)
    
    # Get ad videos
    ad_videos_result = await db.execute(
        select(Video.id).where(ad_video_filter)
    )
    ad_video_ids = [row[0] for row in ad_videos_result.fetchall()]
    
    if not ad_video_ids:
        # No ad videos found
        return {
            "period": period,
            "days": days,
            "totals": {
                "clicks": 0,
                "views": 0,
                "unique_clickers": 0,
                "unique_auth_clickers": 0,
            },
            "metrics": {
                "click_through_rate": 0,
                "avg_clicks_per_view": 0,
                "avg_clicks_per_clicker": 0,
            },
            "clicks_over_time": [],
            "views_over_time": [],
            "top_videos": [],
        }
    
    # Filter clicks and views to only ad videos
    click_filters.append(AdClick.video_id.in_(ad_video_ids))
    view_filters.append(View.video_id.in_(ad_video_ids))
    
    # Total ad clicks
    total_clicks_result = await db.execute(
        select(func.count(AdClick.id)).where(*click_filters)
    )
    total_clicks = total_clicks_result.scalar() or 0
    
    # Total ad video views (views on videos with ad_link)
    total_views_result = await db.execute(
        select(func.count(View.id))
        .join(Video, View.video_id == Video.id)
        .where(*view_filters, Video.ad_link.isnot(None))
    )
    total_views = total_views_result.scalar() or 0
    
    # Unique clickers
    unique_clickers_result = await db.execute(
        select(func.count(distinct(AdClick.clicker_session_id))).where(*click_filters)
    )
    unique_clickers = unique_clickers_result.scalar() or 0
    
    # Unique authenticated clickers
    unique_auth_clickers_result = await db.execute(
        select(func.count(distinct(AdClick.user_id))).where(*click_filters, AdClick.user_id.isnot(None))
    )
    unique_auth_clickers = unique_auth_clickers_result.scalar() or 0
    
    # Calculate metrics
    click_through_rate = (total_clicks / total_views * 100) if total_views > 0 else 0
    avg_clicks_per_view = (total_clicks / total_views) if total_views > 0 else 0
    avg_clicks_per_clicker = (total_clicks / unique_clickers) if unique_clickers > 0 else 0
    
    # Clicks over time
    if period == "day":
        date_trunc = sql_func.date_trunc('day', AdClick.clicked_at).label('date')
    else:  # week
        date_trunc = sql_func.date_trunc('week', AdClick.clicked_at).label('date')
    
    clicks_over_time_query = (
        select(
            date_trunc,
            func.count(AdClick.id).label('count')
        )
        .where(*click_filters)
        .group_by(date_trunc)
        .order_by(date_trunc)
    )
    clicks_over_time_result = await db.execute(clicks_over_time_query)
    clicks_over_time = [
        {
            "date": row[0].isoformat() if row[0] else None,
            "clicks": row[1] or 0
        }
        for row in clicks_over_time_result.fetchall()
    ]
    
    # Views over time (for ad videos)
    if period == "day":
        view_date_trunc = sql_func.date_trunc('day', View.created_at).label('date')
    else:  # week
        view_date_trunc = sql_func.date_trunc('week', View.created_at).label('date')
    
    views_over_time_query = (
        select(
            view_date_trunc,
            func.count(View.id).label('count')
        )
        .join(Video, View.video_id == Video.id)
        .where(*view_filters, Video.ad_link.isnot(None))
        .group_by(view_date_trunc)
        .order_by(view_date_trunc)
    )
    views_over_time_result = await db.execute(views_over_time_query)
    views_over_time = [
        {
            "date": row[0].isoformat() if row[0] else None,
            "views": row[1] or 0
        }
        for row in views_over_time_result.fetchall()
    ]
    
    # Top performing ad videos (by clicks)
    top_videos_query = (
        select(
            Video.id,
            Video.title,
            User.id.label('user_id'),
            User.username,
            func.count(AdClick.id).label('clicks'),
            func.count(distinct(View.id)).label('views')
        )
        .join(User, Video.user_id == User.id)
        .outerjoin(AdClick, AdClick.video_id == Video.id)
        .outerjoin(View, View.video_id == Video.id)
        .where(Video.ad_link.isnot(None))
        .group_by(Video.id, Video.title, User.id, User.username)
        .order_by(func.count(AdClick.id).desc())
        .limit(10)
    )
    
    if video_id:
        top_videos_query = top_videos_query.where(Video.id == video_id)
    
    top_videos_result = await db.execute(top_videos_query)
    top_videos = [
        {
            "id": str(row[0]),
            "title": row[1] or "Untitled",
            "user": {
                "id": str(row[2]),
                "username": row[3]
            },
            "clicks": row[4] or 0,
            "views": row[5] or 0,
            "ctr": ((row[4] or 0) / (row[5] or 1) * 100) if row[5] else 0
        }
        for row in top_videos_result.fetchall()
    ]
    
    return {
        "period": period,
        "days": days,
        "totals": {
            "clicks": total_clicks,
            "views": total_views,
            "unique_clickers": unique_clickers,
            "unique_auth_clickers": unique_auth_clickers,
        },
        "metrics": {
            "click_through_rate": round(click_through_rate, 2),
            "avg_clicks_per_view": round(avg_clicks_per_view, 2),
            "avg_clicks_per_clicker": round(avg_clicks_per_clicker, 2),
        },
        "clicks_over_time": clicks_over_time,
        "views_over_time": views_over_time,
        "top_videos": top_videos,
    }

