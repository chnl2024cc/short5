"""
Share Analytics Endpoints
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
from app.models.share import ShareLink
from app.models.share_click import ShareClick

router = APIRouter()


@router.get("/analytics")
async def get_share_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    period: str = Query("week", description="Group by 'day' or 'week'"),
    days: int = Query(30, description="Number of days to look back"),
    video_id: Optional[str] = Query(None, description="Filter by specific video ID"),
):
    """Get comprehensive share analytics
    
    Returns:
    - Click-through rate (CTR)
    - Total shares created
    - Total clicks
    - Unique clickers
    - Average clicks per share
    - Share conversion rate
    - Most shared videos
    - Shares and clicks over time
    - Top sharers
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Base query filters
    share_filters = [ShareLink.created_at >= start_date]
    click_filters = [ShareClick.clicked_at >= start_date]
    
    if video_id:
        share_filters.append(ShareLink.video_id == video_id)
        click_filters.append(ShareClick.video_id == video_id)
    
    # Total shares created
    total_shares_result = await db.execute(
        select(func.count(ShareLink.id)).where(*share_filters)
    )
    total_shares = total_shares_result.scalar() or 0
    
    # Total clicks
    total_clicks_result = await db.execute(
        select(func.count(ShareClick.id)).where(*click_filters)
    )
    total_clicks = total_clicks_result.scalar() or 0
    
    # Unique clickers
    unique_clickers_result = await db.execute(
        select(func.count(distinct(ShareClick.clicker_session_id))).where(*click_filters)
    )
    unique_clickers = unique_clickers_result.scalar() or 0
    
    # Shares with at least one click
    shares_with_clicks_result = await db.execute(
        select(func.count(distinct(ShareClick.share_link_id))).where(*click_filters)
    )
    shares_with_clicks = shares_with_clicks_result.scalar() or 0
    
    # Calculate metrics
    click_through_rate = (total_clicks / total_shares * 100) if total_shares > 0 else 0
    avg_clicks_per_share = (total_clicks / total_shares) if total_shares > 0 else 0
    share_conversion_rate = (shares_with_clicks / total_shares * 100) if total_shares > 0 else 0
    avg_clicks_per_clicker = (total_clicks / unique_clickers) if unique_clickers > 0 else 0
    
    # Shares over time
    if period == "day":
        date_trunc = sql_func.date_trunc('day', ShareLink.created_at).label('date')
    else:  # week
        date_trunc = sql_func.date_trunc('week', ShareLink.created_at).label('date')
    
    shares_over_time_query = (
        select(
            date_trunc,
            func.count(ShareLink.id).label('count')
        )
        .where(*share_filters)
        .group_by(date_trunc)
        .order_by(date_trunc)
    )
    shares_over_time_result = await db.execute(shares_over_time_query)
    shares_over_time = [
        {
            "date": row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date),
            "shares": row.count
        }
        for row in shares_over_time_result.all()
    ]
    
    # Clicks over time
    clicks_date_trunc = sql_func.date_trunc('day' if period == 'day' else 'week', ShareClick.clicked_at).label('date')
    clicks_over_time_query = (
        select(
            clicks_date_trunc,
            func.count(ShareClick.id).label('count')
        )
        .where(*click_filters)
        .group_by(clicks_date_trunc)
        .order_by(clicks_date_trunc)
    )
    clicks_over_time_result = await db.execute(clicks_over_time_query)
    clicks_over_time = [
        {
            "date": row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date),
            "clicks": row.count
        }
        for row in clicks_over_time_result.all()
    ]
    
    # Most shared videos
    most_shared_query = (
        select(
            Video.id,
            Video.title,
            func.count(ShareLink.id).label('share_count')
        )
        .join(ShareLink, ShareLink.video_id == Video.id)
        .where(*share_filters)
        .group_by(Video.id, Video.title)
        .order_by(func.count(ShareLink.id).desc())
        .limit(10)
    )
    most_shared_result = await db.execute(most_shared_query)
    most_shared_videos = [
        {
            "video_id": str(row.id),
            "title": row.title,
            "share_count": row.share_count
        }
        for row in most_shared_result.all()
    ]
    
    # Videos with most clicks
    most_clicked_query = (
        select(
            Video.id,
            Video.title,
            func.count(ShareClick.id).label('click_count')
        )
        .join(ShareClick, ShareClick.video_id == Video.id)
        .where(*click_filters)
        .group_by(Video.id, Video.title)
        .order_by(func.count(ShareClick.id).desc())
        .limit(10)
    )
    most_clicked_result = await db.execute(most_clicked_query)
    most_clicked_videos = [
        {
            "video_id": str(row.id),
            "title": row.title,
            "click_count": row.click_count
        }
        for row in most_clicked_result.all()
    ]
    
    # Top sharers (by number of shares created)
    top_sharers_query = (
        select(
            ShareLink.sharer_session_id,
            func.count(ShareLink.id).label('share_count')
        )
        .where(*share_filters)
        .group_by(ShareLink.sharer_session_id)
        .order_by(func.count(ShareLink.id).desc())
        .limit(10)
    )
    top_sharers_result = await db.execute(top_sharers_query)
    top_sharers = [
        {
            "sharer_session_id": str(row.sharer_session_id),
            "share_count": row.share_count
        }
        for row in top_sharers_result.all()
    ]
    
    # Average time between share creation and first click
    # Get first click for each share link
    first_clicks_subquery = (
        select(
            ShareClick.share_link_id,
            func.min(ShareClick.clicked_at).label('first_click_at')
        )
        .where(*click_filters)
        .group_by(ShareClick.share_link_id)
        .subquery()
    )
    
    time_to_first_click_query = (
        select(
            func.avg(
                func.extract('epoch', first_clicks_subquery.c.first_click_at - ShareLink.created_at) / 3600
            ).label('avg_hours')
        )
        .join(first_clicks_subquery, ShareLink.id == first_clicks_subquery.c.share_link_id)
        .where(*share_filters)
    )
    
    time_to_first_click_result = await db.execute(time_to_first_click_query)
    avg_time_to_first_click_hours = time_to_first_click_result.scalar() or 0
    
    return {
        "period": period,
        "days": days,
        "video_id": video_id,
        "summary": {
            "total_shares": total_shares,
            "total_clicks": total_clicks,
            "unique_clickers": unique_clickers,
            "shares_with_clicks": shares_with_clicks,
        },
        "metrics": {
            "click_through_rate": round(click_through_rate, 2),  # Percentage
            "avg_clicks_per_share": round(avg_clicks_per_share, 2),
            "share_conversion_rate": round(share_conversion_rate, 2),  # Percentage of shares that got clicks
            "avg_clicks_per_clicker": round(avg_clicks_per_clicker, 2),
            "avg_time_to_first_click_hours": round(avg_time_to_first_click_hours, 2),
        },
        "over_time": {
            "shares": shares_over_time,
            "clicks": clicks_over_time,
        },
        "top_videos": {
            "most_shared": most_shared_videos,
            "most_clicked": most_clicked_videos,
        },
        "top_sharers": top_sharers,
    }


@router.get("/stats")
async def get_share_stats(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get quick share statistics (no time filtering)"""
    
    # Total shares
    total_shares_result = await db.execute(select(func.count(ShareLink.id)))
    total_shares = total_shares_result.scalar() or 0
    
    # Total clicks
    total_clicks_result = await db.execute(select(func.count(ShareClick.id)))
    total_clicks = total_clicks_result.scalar() or 0
    
    # Unique clickers
    unique_clickers_result = await db.execute(
        select(func.count(distinct(ShareClick.clicker_session_id)))
    )
    unique_clickers = unique_clickers_result.scalar() or 0
    
    # Shares with clicks
    shares_with_clicks_result = await db.execute(
        select(func.count(distinct(ShareClick.share_link_id)))
    )
    shares_with_clicks = shares_with_clicks_result.scalar() or 0
    
    # Calculate metrics
    click_through_rate = (total_clicks / total_shares * 100) if total_shares > 0 else 0
    avg_clicks_per_share = (total_clicks / total_shares) if total_shares > 0 else 0
    share_conversion_rate = (shares_with_clicks / total_shares * 100) if total_shares > 0 else 0
    
    return {
        "total_shares": total_shares,
        "total_clicks": total_clicks,
        "unique_clickers": unique_clickers,
        "shares_with_clicks": shares_with_clicks,
        "click_through_rate": round(click_through_rate, 2),
        "avg_clicks_per_share": round(avg_clicks_per_share, 2),
        "share_conversion_rate": round(share_conversion_rate, 2),
    }

