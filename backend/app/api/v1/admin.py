"""
Admin Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String, and_, or_
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin_user
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.models.report import Report, ReportType, ReportStatus
from app.models.vote import Vote, VoteDirection
from app.models.view import View
from app.schemas.video import VideoResponse, UserBasic, VideoStats

router = APIRouter()


# Request/Response Models
class RejectVideoRequest(BaseModel):
    reason: Optional[str] = None


class ResolveReportRequest(BaseModel):
    action: str  # "resolve" or "dismiss"
    notes: Optional[str] = None


# Video Moderation Endpoints
@router.get("/videos")
async def get_all_videos(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    cursor: Optional[str] = None,
    limit: int = 20,
    status: Optional[str] = None,
):
    """Get all videos with optional status filter (admin only)"""
    query = select(Video, User).join(User, Video.user_id == User.id)
    
    # Filter by status if provided
    if status:
        try:
            video_status = VideoStatus(status.lower())
            query = query.where(Video.status == video_status)
        except ValueError:
            pass  # Invalid status, ignore filter
    
    query = query.order_by(Video.created_at.desc())
    
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
        
        videos.append({
            "id": str(video.id),
            "title": video.title,
            "description": video.description,
            "status": video.status.value,
            "thumbnail": video.thumbnail,
            "url_mp4": video.url_mp4,
            "duration_seconds": video.duration_seconds,
            "error_reason": video.error_reason,
            "user": {
                "id": str(user.id),
                "username": user.username,
            },
            "stats": {
                "likes": likes_count.scalar() or 0,
                "views": views_count.scalar() or 0,
            },
            "created_at": video.created_at.isoformat() if video.created_at else None,
        })
    
    next_cursor = rows[-1][0].created_at.isoformat() if rows else None
    has_more = len(rows) == limit
    
    return {
        "videos": videos,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/videos/pending")
async def get_pending_videos(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    cursor: Optional[str] = None,
    limit: int = 20,
):
    """Get videos pending moderation (processing or uploading status)"""
    query = (
        select(Video, User)
        .join(User, Video.user_id == User.id)
        .where(
            or_(
                Video.status == VideoStatus.PROCESSING,
                Video.status == VideoStatus.UPLOADING,
            )
        )
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
        
        videos.append({
            "id": str(video.id),
            "title": video.title,
            "description": video.description,
            "status": video.status.value,
            "thumbnail": video.thumbnail,
            "url_mp4": video.url_mp4,
            "duration_seconds": video.duration_seconds,
            "user": {
                "id": str(user.id),
                "username": user.username,
            },
            "stats": {
                "likes": likes_count.scalar() or 0,
                "views": views_count.scalar() or 0,
            },
            "created_at": video.created_at,
        })
    
    next_cursor = rows[-1][0].created_at.isoformat() if rows else None
    has_more = len(rows) == limit
    
    return {
        "videos": videos,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.post("/videos/{video_id}/approve")
async def approve_video(
    video_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a video (set status to ready)"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    if video.status == VideoStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video is already approved",
        )
    
    video.status = VideoStatus.READY
    await db.commit()
    await db.refresh(video)
    
    return {
        "message": "Video approved",
        "video_id": str(video.id),
        "status": video.status.value,
    }


@router.post("/videos/{video_id}/reject")
async def reject_video(
    video_id: str,
    request: RejectVideoRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a video (set status to rejected)"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    if video.status == VideoStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video is already rejected",
        )
    
    video.status = VideoStatus.REJECTED
    await db.commit()
    await db.refresh(video)
    
    return {
        "message": "Video rejected",
        "video_id": str(video.id),
        "status": video.status.value,
        "reason": request.reason,
    }


@router.delete("/videos/{video_id}")
async def delete_video_admin(
    video_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a video (admin only - comprehensive deletion)"""
    from app.services.video_deletion import VideoDeletionService
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    video_deletion_service = VideoDeletionService()
    try:
        deletion_result = await video_deletion_service.delete_video(str(video.id), db, video)
        return {
            "message": "Video deleted successfully",
            "video_id": str(video.id),
            "deletion_result": deletion_result,
        }
    except Exception as e:
        error_message = str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete video: {error_message}",
        )


# Reports Management Endpoints
@router.get("/reports")
async def get_reports(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = 20,
):
    """Get all reports (admin only)"""
    query = select(Report, User).join(User, Report.reporter_id == User.id)
    
    # Filter by status
    if status:
        try:
            report_status = ReportStatus(status.lower())
            query = query.where(Report.status == report_status)
        except ValueError:
            pass  # Invalid status, ignore filter
    
    query = query.order_by(Report.created_at.desc())
    
    if cursor:
        try:
            from datetime import datetime
            cursor_time = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            query = query.where(Report.created_at < cursor_time)
        except Exception:
            pass
    
    query = query.limit(min(limit, 100))
    
    result = await db.execute(query)
    rows = result.all()
    
    reports = []
    for report, reporter in rows:
        # Get target info (video or user)
        target_info = None
        if report.report_type == ReportType.VIDEO:
            video_result = await db.execute(
                select(Video, User)
                .join(User, Video.user_id == User.id)
                .where(Video.id == report.target_id)
            )
            video_row = video_result.first()
            if video_row:
                video, video_user = video_row
                target_info = {
                    "id": str(video.id),
                    "title": video.title,
                    "user": {
                        "id": str(video_user.id),
                        "username": video_user.username,
                    },
                }
        elif report.report_type == ReportType.USER:
            user_result = await db.execute(
                select(User).where(User.id == report.target_id)
            )
            target_user = user_result.scalar_one_or_none()
            if target_user:
                target_info = {
                    "id": str(target_user.id),
                    "username": target_user.username,
                }
        
        resolver_info = None
        if report.resolved_by:
            resolver_result = await db.execute(
                select(User).where(User.id == report.resolved_by)
            )
            resolver = resolver_result.scalar_one_or_none()
            if resolver:
                resolver_info = {
                    "id": str(resolver.id),
                    "username": resolver.username,
                }
        
        reports.append({
            "id": str(report.id),
            "type": report.report_type.value,
            "target_id": str(report.target_id),
            "target": target_info,
            "reason": report.reason,
            "status": report.status.value,
            "reporter": {
                "id": str(reporter.id),
                "username": reporter.username,
            },
            "resolver": resolver_info,
            "resolved_at": report.resolved_at,
            "created_at": report.created_at,
        })
    
    next_cursor = rows[-1][0].created_at.isoformat() if rows else None
    has_more = len(rows) == limit
    
    return {
        "reports": reports,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.post("/reports/{report_id}/resolve")
async def resolve_report(
    report_id: str,
    request: ResolveReportRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve or dismiss a report"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    if report.status != ReportStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is already {report.status.value}",
        )
    
    from datetime import datetime, timezone
    
    if request.action.lower() == "resolve":
        report.status = ReportStatus.RESOLVED
    elif request.action.lower() == "dismiss":
        report.status = ReportStatus.DISMISSED
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'resolve' or 'dismiss'",
        )
    
    report.resolved_by = current_user.id
    report.resolved_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(report)
    
    return {
        "message": f"Report {request.action.lower()}ed",
        "report_id": str(report.id),
        "status": report.status.value,
    }


@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get admin dashboard statistics"""
    # Total users
    users_count = await db.execute(select(func.count(User.id)))
    total_users = users_count.scalar() or 0
    
    # Total videos
    videos_count = await db.execute(select(func.count(Video.id)))
    total_videos = videos_count.scalar() or 0
    
    # Videos by status
    videos_by_status = {}
    for status in VideoStatus:
        count_result = await db.execute(
            select(func.count(Video.id)).where(Video.status == status)
        )
        videos_by_status[status.value] = count_result.scalar() or 0
    
    # Pending reports - cast to string for PostgreSQL enum compatibility
    pending_reports_count = await db.execute(
        select(func.count(Report.id)).where(
            cast(Report.status, String) == ReportStatus.PENDING.value
        )
    )
    pending_reports = pending_reports_count.scalar() or 0
    
    # Total reports
    total_reports_count = await db.execute(select(func.count(Report.id)))
    total_reports = total_reports_count.scalar() or 0
    
    return {
        "users": {
            "total": total_users,
        },
        "videos": {
            "total": total_videos,
            "by_status": videos_by_status,
        },
        "reports": {
            "total": total_reports,
            "pending": pending_reports,
        },
    }


@router.get("/analytics")
async def get_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    period: str = "week",  # "day" or "week"
    days: int = 30,  # Number of days to look back
):
    """Get analytics data (views, likes) grouped by day or week"""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func as sql_func
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Group by day or week
    if period == "day":
        date_trunc = sql_func.date_trunc('day', View.created_at).label('date')
        date_format = '%Y-%m-%d'
    else:  # week
        date_trunc = sql_func.date_trunc('week', View.created_at).label('date')
        date_format = '%Y-W%V'
    
    # Get views per period
    views_query = (
        select(
            date_trunc,
            func.count(View.id).label('count')
        )
        .where(View.created_at >= start_date)
        .group_by(date_trunc)
        .order_by(date_trunc)
    )
    views_result = await db.execute(views_query)
    views_data = views_result.all()
    
    # Get likes per period
    likes_date_trunc = sql_func.date_trunc('day' if period == 'day' else 'week', Vote.created_at).label('date')
    likes_query = (
        select(
            likes_date_trunc,
            func.count(Vote.id).label('count')
        )
        .where(
            Vote.created_at >= start_date,
            cast(Vote.direction, String) == "like"
        )
        .group_by(likes_date_trunc)
        .order_by(likes_date_trunc)
    )
    likes_result = await db.execute(likes_query)
    likes_data = likes_result.all()
    
    # Get new videos per period
    videos_date_trunc = sql_func.date_trunc('day' if period == 'day' else 'week', Video.created_at).label('date')
    videos_query = (
        select(
            videos_date_trunc,
            func.count(Video.id).label('count')
        )
        .where(Video.created_at >= start_date)
        .group_by(videos_date_trunc)
        .order_by(videos_date_trunc)
    )
    videos_result = await db.execute(videos_query)
    videos_data = videos_result.all()
    
    # Get new users per period
    users_date_trunc = sql_func.date_trunc('day' if period == 'day' else 'week', User.created_at).label('date')
    users_query = (
        select(
            users_date_trunc,
            func.count(User.id).label('count')
        )
        .where(User.created_at >= start_date)
        .group_by(users_date_trunc)
        .order_by(users_date_trunc)
    )
    users_result = await db.execute(users_query)
    users_data = users_result.all()
    
    # Format dates and combine data
    analytics = []
    all_dates = set()
    
    for row in views_data:
        date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
        all_dates.add(date_str)
    for row in likes_data:
        date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
        all_dates.add(date_str)
    for row in videos_data:
        date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
        all_dates.add(date_str)
    for row in users_data:
        date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
        all_dates.add(date_str)
    
    # Create lookup dictionaries
    views_dict = {}
    for row in views_data:
        date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
        views_dict[date_str] = row.count
    
    likes_dict = {}
    for row in likes_data:
        date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
        likes_dict[date_str] = row.count
    
    videos_dict = {}
    for row in videos_data:
        date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
        videos_dict[date_str] = row.count
    
    users_dict = {}
    for row in users_data:
        date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
        users_dict[date_str] = row.count
    
    # Combine into sorted list
    for date_str in sorted(all_dates):
        analytics.append({
            "date": date_str,
            "views": views_dict.get(date_str, 0),
            "likes": likes_dict.get(date_str, 0),
            "videos": videos_dict.get(date_str, 0),
            "users": users_dict.get(date_str, 0),
        })
    
    # Calculate totals and averages
    total_views = sum(item["views"] for item in analytics)
    total_likes = sum(item["likes"] for item in analytics)
    total_new_videos = sum(item["videos"] for item in analytics)
    total_new_users = sum(item["users"] for item in analytics)
    
    avg_views_per_period = total_views / len(analytics) if analytics else 0
    avg_likes_per_period = total_likes / len(analytics) if analytics else 0
    
    # Get top videos by views
    top_views_subquery = (
        select(
            View.video_id,
            func.count(View.id).label('view_count')
        )
        .where(View.created_at >= start_date)
        .group_by(View.video_id)
        .order_by(func.count(View.id).desc())
        .limit(10)
        .subquery()
    )
    
    top_views_query = (
        select(Video, User, top_views_subquery.c.view_count)
        .join(User, Video.user_id == User.id)
        .join(top_views_subquery, Video.id == top_views_subquery.c.video_id)
        .order_by(top_views_subquery.c.view_count.desc())
    )
    top_views_result = await db.execute(top_views_query)
    top_views_rows = top_views_result.all()
    
    top_videos_by_views = []
    for video, user, view_count in top_views_rows:
        # Get likes for this video
        likes_count_result = await db.execute(
            select(func.count(Vote.id)).where(
                Vote.video_id == video.id,
                cast(Vote.direction, String) == "like"
            )
        )
        likes_count = likes_count_result.scalar() or 0
        
        top_videos_by_views.append({
            "id": str(video.id),
            "title": video.title,
            "user": {
                "id": str(user.id),
                "username": user.username,
            },
            "views": view_count or 0,
            "likes": likes_count,
            "created_at": video.created_at.isoformat() if video.created_at else None,
        })
    
    # Get top videos by likes
    top_likes_subquery = (
        select(
            Vote.video_id,
            func.count(Vote.id).label('like_count')
        )
        .where(
            Vote.created_at >= start_date,
            cast(Vote.direction, String) == "like"
        )
        .group_by(Vote.video_id)
        .order_by(func.count(Vote.id).desc())
        .limit(10)
        .subquery()
    )
    
    top_likes_query = (
        select(Video, User, top_likes_subquery.c.like_count)
        .join(User, Video.user_id == User.id)
        .join(top_likes_subquery, Video.id == top_likes_subquery.c.video_id)
        .order_by(top_likes_subquery.c.like_count.desc())
    )
    top_likes_result = await db.execute(top_likes_query)
    top_likes_rows = top_likes_result.all()
    
    top_videos_by_likes = []
    for video, user, like_count in top_likes_rows:
        # Get views for this video
        views_count_result = await db.execute(
            select(func.count(View.id)).where(View.video_id == video.id)
        )
        views_count = views_count_result.scalar() or 0
        
        top_videos_by_likes.append({
            "id": str(video.id),
            "title": video.title,
            "user": {
                "id": str(user.id),
                "username": user.username,
            },
            "views": views_count,
            "likes": like_count or 0,
            "created_at": video.created_at.isoformat() if video.created_at else None,
        })
    
    # Get most active users (by videos uploaded in period)
    active_users_query = (
        select(
            User,
            func.count(Video.id).label('video_count')
        )
        .join(Video, User.id == Video.user_id)
        .where(Video.created_at >= start_date)
        .group_by(User.id)
        .order_by(func.count(Video.id).desc())
        .limit(10)
    )
    active_users_result = await db.execute(active_users_query)
    active_users_rows = active_users_result.all()
    
    most_active_users = []
    for user, video_count in active_users_rows:
        most_active_users.append({
            "id": str(user.id),
            "username": user.username,
            "videos_uploaded": video_count or 0,
        })
    
    # Calculate engagement rate (likes/views ratio)
    engagement_rate = (total_likes / total_views * 100) if total_views > 0 else 0
    
    # Calculate growth trends (compare first half vs second half of period)
    if len(analytics) > 1:
        midpoint = len(analytics) // 2
        first_half_views = sum(item["views"] for item in analytics[:midpoint])
        second_half_views = sum(item["views"] for item in analytics[midpoint:])
        first_half_likes = sum(item["likes"] for item in analytics[:midpoint])
        second_half_likes = sum(item["likes"] for item in analytics[midpoint:])
        
        views_growth = ((second_half_views - first_half_views) / first_half_views * 100) if first_half_views > 0 else 0
        likes_growth = ((second_half_likes - first_half_likes) / first_half_likes * 100) if first_half_likes > 0 else 0
    else:
        views_growth = 0
        likes_growth = 0
    
    return {
        "period": period,
        "days": days,
        "analytics": analytics,
        "totals": {
            "views": total_views,
            "likes": total_likes,
            "new_videos": total_new_videos,
            "new_users": total_new_users,
        },
        "averages": {
            "views_per_period": round(avg_views_per_period, 2),
            "likes_per_period": round(avg_likes_per_period, 2),
        },
        "top_videos_by_views": top_videos_by_views,
        "top_videos_by_likes": top_videos_by_likes,
        "most_active_users": most_active_users,
        "engagement_rate": round(engagement_rate, 2),
        "growth": {
            "views_growth": round(views_growth, 2),
            "likes_growth": round(likes_growth, 2),
        },
    }


# User Management Endpoints
@router.get("/users")
async def get_users(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    cursor: Optional[str] = None,
    limit: int = 50,
    search: Optional[str] = None,
):
    """Get all users (admin only)"""
    query = select(User)
    
    # Search by username or email
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(User.username).like(search_term),
                func.lower(User.email).like(search_term),
            )
        )
    
    query = query.order_by(User.created_at.desc())
    
    if cursor:
        try:
            from datetime import datetime
            cursor_time = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            query = query.where(User.created_at < cursor_time)
        except Exception:
            pass
    
    query = query.limit(min(limit, 100))
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Get stats for each user
    users_data = []
    for user in users:
        # Get video count
        videos_count = await db.execute(
            select(func.count(Video.id)).where(Video.user_id == user.id)
        )
        video_count = videos_count.scalar() or 0
        
        users_data.append({
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "video_count": video_count,
        })
    
    next_cursor = users[-1].created_at.isoformat() if users else None
    has_more = len(users) == limit
    
    return {
        "users": users_data,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed user information (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Get user stats
    videos_count = await db.execute(
        select(func.count(Video.id)).where(Video.user_id == user.id)
    )
    video_count = videos_count.scalar() or 0
    
    # Get videos by status
    videos_by_status = {}
    for video_status in VideoStatus:
        count_result = await db.execute(
            select(func.count(Video.id)).where(
                and_(Video.user_id == user.id, Video.status == video_status)
            )
        )
        videos_by_status[video_status.value] = count_result.scalar() or 0
    
    # Get reports made by this user
    reports_made_count = await db.execute(
        select(func.count(Report.id)).where(Report.reporter_id == user.id)
    )
    reports_made = reports_made_count.scalar() or 0
    
    # Get reports against this user
    reports_against_count = await db.execute(
        select(func.count(Report.id)).where(
            and_(
                Report.report_type == ReportType.USER,
                Report.target_id == user.id
            )
        )
    )
    reports_against = reports_against_count.scalar() or 0
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "stats": {
            "videos": {
                "total": video_count,
                "by_status": videos_by_status,
            },
            "reports_made": reports_made,
            "reports_against": reports_against,
        },
    }


class UpdateUserRequest(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user (ban/unban, admin status)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent self-modification of admin status
    if user.id == current_user.id and request.is_admin is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own admin status",
        )
    
    # Prevent self-ban
    if user.id == current_user.id and request.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ban yourself",
        )
    
    if request.is_active is not None:
        user.is_active = request.is_active
    if request.is_admin is not None:
        user.is_admin = request.is_admin
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "message": "User updated",
        "user_id": str(user.id),
        "is_active": user.is_active,
        "is_admin": user.is_admin,
    }
