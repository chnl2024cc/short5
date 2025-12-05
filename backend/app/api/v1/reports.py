"""
Reports Endpoints (User-facing)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.dependencies import get_current_user_required
from app.models.user import User
from app.models.video import Video
from app.models.report import Report, ReportType, ReportStatus

router = APIRouter()


class CreateReportRequest(BaseModel):
    report_type: str  # "video" or "user"
    target_id: str  # video_id or user_id
    reason: Optional[str] = None


@router.post("")
async def create_report(
    request: CreateReportRequest,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Create a report (complaint) about a video or user"""
    # Validate report type
    try:
        report_type = ReportType(request.report_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report_type. Must be 'video' or 'user'",
        )
    
    # Validate target exists
    if report_type == ReportType.VIDEO:
        result = await db.execute(select(Video).where(Video.id == request.target_id))
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )
        # Prevent reporting own video
        if target.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot report your own video",
            )
    else:  # ReportType.USER
        result = await db.execute(select(User).where(User.id == request.target_id))
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        # Prevent reporting yourself
        if target.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot report yourself",
            )
    
    # Check if user already reported this target
    existing_report = await db.execute(
        select(Report).where(
            Report.reporter_id == current_user.id,
            Report.report_type == report_type,
            Report.target_id == request.target_id,
        )
    )
    if existing_report.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reported this " + request.report_type,
        )
    
    # Create report
    report = Report(
        reporter_id=current_user.id,
        report_type=report_type,
        target_id=request.target_id,
        reason=request.reason,
        status=ReportStatus.PENDING,
    )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return {
        "message": "Report submitted successfully",
        "report_id": str(report.id),
        "status": report.status.value,
    }

