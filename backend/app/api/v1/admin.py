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
            "url_hls": video.url_hls,
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
    
    # Pending reports
    pending_reports_count = await db.execute(
        select(func.count(Report.id)).where(Report.status == ReportStatus.PENDING)
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
