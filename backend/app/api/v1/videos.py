"""
Video Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String, delete
from sqlalchemy.exc import IntegrityError
from typing import Optional
import uuid
import logging
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.dependencies import get_current_user_required, get_current_user
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.models.vote import Vote, VoteDirection
from app.models.view import View
from app.models.user_liked_video import UserLikedVideo
from app.schemas.video import (
    VideoResponse,
    VideoStats,
    UserBasic,
    VoteRequest,
    VoteResponse,
    ViewRequest,
    ViewResponse,
)
from app.celery_app import celery_app
from app.services.video_deletion import video_deletion_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Upload directories - clear structure
UPLOAD_DIR = Path("/app/uploads")
ORIGINALS_DIR = UPLOAD_DIR / "originals"  # Original uploaded files
PROCESSED_DIR = UPLOAD_DIR / "processed"  # Processed files (MP4, thumbnails)

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
ORIGINALS_DIR.mkdir(exist_ok=True, parents=True)
PROCESSED_DIR.mkdir(exist_ok=True, parents=True)


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Upload a video file"""
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_VIDEO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed: {', '.join(settings.ALLOWED_VIDEO_FORMATS)}",
        )
    
    # Read file to check size
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB",
        )
    
    # Create video record
    video = Video(
        user_id=current_user.id,
        title=title,
        description=description,
        status=VideoStatus.UPLOADING,
        file_size_bytes=file_size,
        original_filename=file.filename,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    # Save original file
    video_filename = f"{video.id}{file_ext}"
    file_path = ORIGINALS_DIR / video_filename
    file_path.write_bytes(content)
    
    # Update video with file path
    video.status = VideoStatus.PROCESSING
    await db.commit()
    
    # Trigger video processing task
    # Use send_task to send to video_worker (different Celery app)
    # The task is registered in video_worker as "process_video"
    try:
        # Pre-task logging: log key state before attempting to send
        logger.info(
            f"[VIDEO_TASK] Preparing to send task for video {video.id}: "
            f"file_path={file_path}, file_size={file_size} bytes, "
            f"file_exists={file_path.exists()}, celery_app={type(celery_app).__name__}"
        )
        
        # Try different task name formats to ensure compatibility
        # The worker's Celery app is named "worker", so we need to use the fully qualified name
        # Try: "worker.process_video" first (fully qualified), then fallback to "process_video"
        task_names_to_try = ["worker.process_video", "process_video"]
        
        # Check Celery app state before sending
        if not hasattr(celery_app, 'send_task'):
            raise AttributeError(f"Celery app missing send_task method: {type(celery_app)}")
        
        # Wait for worker to be ready (especially important for first upload)
        # Retry up to 3 times with exponential backoff
        import time
        max_retries = 3
        retry_delay = 2  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                # Check if worker is available and has registered the task
                inspect = celery_app.control.inspect(timeout=2.0)
                registered_tasks = inspect.registered()
                
                if registered_tasks:
                    # Check if any worker has process_video task registered (check all possible names)
                    has_process_video = False
                    registered_task_names = []
                    for tasks in registered_tasks.values():
                        registered_task_names.extend(tasks)
                        if any('process_video' in str(task) for task in tasks):
                            has_process_video = True
                            break
                    
                    if has_process_video:
                        logger.info(f"[VIDEO_TASK] Worker ready with 'process_video' task registered (attempt {attempt + 1})")
                        logger.info(f"[VIDEO_TASK] Available task names: {registered_task_names[:10]}...")  # Log first 10
                        break
                    else:
                        if attempt < max_retries - 1:
                            logger.warning(f"[VIDEO_TASK] Worker found but 'process_video' not registered yet. Registered tasks: {registered_task_names[:10]}..., retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            logger.warning(f"[VIDEO_TASK] Worker found but 'process_video' task not registered after {max_retries} attempts. Registered: {registered_task_names}, sending anyway")
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"[VIDEO_TASK] No workers found, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.warning(f"[VIDEO_TASK] No workers found after {max_retries} attempts, sending task anyway (will be queued)")
            except Exception as inspect_error:
                if attempt < max_retries - 1:
                    logger.warning(f"[VIDEO_TASK] Could not inspect workers (attempt {attempt + 1}/{max_retries}): {inspect_error}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.warning(f"[VIDEO_TASK] Could not inspect workers after {max_retries} attempts: {inspect_error}, sending task anyway")
        
        # Try sending with different task name formats
        # Note: send_task should work even if task isn't registered in this app
        # The error might occur if Celery tries to validate the task name
        result = None
        last_error = None
        
        # Use send_task with the task name - this should work across apps
        # If it fails, it's likely a configuration issue
        task_name = "process_video"  # Use simple name first
        
        try:
            # send_task should bypass local task registration
            # Note: We use ignore_result=True but still check result.state for immediate failures
            result = celery_app.send_task(
                task_name,
                args=[str(video.id), str(file_path)],
                queue="celery",  # Explicitly specify queue - video_worker listens to this
                # Don't require result - task runs asynchronously
                ignore_result=True,
            )
            logger.info(f"[VIDEO_TASK] Successfully sent task with name '{task_name}'")
            
            # Note: With ignore_result=True, result.state may not be immediately accurate
            # The task is sent to the queue and will be processed asynchronously
            # We don't check state here to avoid blocking or false negatives
        except Exception as send_error:
            # If simple name fails, try fully qualified name
            error_str = str(send_error).lower()
            if "notregistered" in error_str or "not registered" in error_str:
                logger.warning(f"[VIDEO_TASK] Task '{task_name}' not recognized, trying fully qualified name...")
                try:
                    # Try with app prefix
                    task_name = "worker.process_video"
                    result = celery_app.send_task(
                        task_name,
                        args=[str(video.id), str(file_path)],
                        queue="celery",
                        ignore_result=True,
                    )
                    logger.info(f"[VIDEO_TASK] Successfully sent task with fully qualified name '{task_name}'")
                except Exception as retry_error:
                    last_error = retry_error
                    logger.error(f"[VIDEO_TASK] Failed to send task with both name formats. Last error: {retry_error}")
                    raise
            else:
                last_error = send_error
                logger.error(f"[VIDEO_TASK] Failed to send task: {send_error}")
                raise
        
        if not result:
            raise Exception(f"Failed to send task. Last error: {last_error}")
        
        # Post-task logging: verify result and log success details
        if not result or not hasattr(result, 'id'):
            logger.error(
                f"[VIDEO_TASK] Task sent but invalid result for video {video.id}: "
                f"result_type={type(result)}, result={result}"
            )
        else:
            # Note: With ignore_result=True, checking result.state immediately may not be accurate
            # The task is queued and will be processed asynchronously by the video_worker
            # We log the task ID for tracking, but don't check state to avoid false negatives
            logger.info(
                f"[VIDEO_TASK] Task successfully queued for video {video.id}: "
                f"task_id={result.id}, task_name={task_name}, queue=celery, "
                f"file_path={file_path}"
            )
            
            # Try to check if workers are available (non-blocking check)
            try:
                inspect = celery_app.control.inspect(timeout=1.0)
                active_workers = inspect.active()
                registered_tasks = inspect.registered()
                
                if active_workers:
                    logger.info(f"[VIDEO_TASK] Active workers found: {list(active_workers.keys())}")
                else:
                    logger.warning(f"[VIDEO_TASK] No active workers detected - task may not be processed immediately")
                    
                if registered_tasks:
                    # Check if any worker has process_video task registered
                    has_process_video = any(
                        'process_video' in tasks 
                        for tasks in registered_tasks.values()
                    )
                    if has_process_video:
                        logger.info(f"[VIDEO_TASK] 'process_video' task is registered on at least one worker")
                    else:
                        logger.warning(f"[VIDEO_TASK] 'process_video' task not found in registered tasks. Registered: {registered_tasks}")
            except Exception as inspect_error:
                # Non-critical - just log warning
                logger.warning(f"[VIDEO_TASK] Could not inspect workers (this is non-critical): {inspect_error}")
    except AttributeError as e:
        logger.error(
            f"[VIDEO_TASK] Celery app configuration error for video {video.id}: {e}",
            exc_info=True
        )
    except Exception as e:
        logger.error(
            f"[VIDEO_TASK] Failed to send video processing task for video {video.id}: "
            f"error_type={type(e).__name__}, error={e}, "
            f"file_path={file_path}, file_exists={file_path.exists() if file_path else False}",
            exc_info=True
        )
        # Don't fail the upload, but log the error
        # The video will remain in PROCESSING status and can be retried
    
    return {
        "video_id": str(video.id),
        "status": "processing",
        "message": "Video upload accepted, processing started",
    }


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get video details"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Get user
    user_result = await db.execute(select(User).where(User.id == video.user_id))
    user = user_result.scalar_one()
    
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
    
    return VideoResponse(
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


@router.post("/{video_id}/vote", response_model=VoteResponse)
async def vote_on_video(
    video_id: str,
    vote_data: VoteRequest,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Swipe/vote on a video (Like or Not-Like)"""
    # Check if video exists
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Check if already voted - allow updating vote direction
    existing_vote_result = await db.execute(
        select(Vote).where(
            Vote.user_id == current_user.id,
            Vote.video_id == video.id,
        )
    )
    existing_vote = existing_vote_result.scalar_one_or_none()
    
    # Determine new direction
    new_direction = VoteDirection.LIKE if vote_data.direction == "like" else VoteDirection.NOT_LIKE
    
    if existing_vote:
        # User already voted - update the vote direction
        old_direction = existing_vote.direction
        existing_vote.direction = new_direction
        
        # Handle user_liked_videos based on direction change
        if old_direction == VoteDirection.LIKE and new_direction == VoteDirection.NOT_LIKE:
            # Changed from like to not_like - remove from liked videos
            delete_stmt = delete(UserLikedVideo).where(
                UserLikedVideo.user_id == current_user.id,
                UserLikedVideo.video_id == video.id,
            )
            await db.execute(delete_stmt)
        elif old_direction == VoteDirection.NOT_LIKE and new_direction == VoteDirection.LIKE:
            # Changed from not_like to like - add to liked videos (if not already there)
            existing_liked_result = await db.execute(
                select(UserLikedVideo).where(
                    UserLikedVideo.user_id == current_user.id,
                    UserLikedVideo.video_id == video.id,
                )
            )
            if not existing_liked_result.scalar_one_or_none():
                liked_video = UserLikedVideo(
                    user_id=current_user.id,
                    video_id=video.id,
                )
                db.add(liked_video)
        # If direction is the same, no changes needed
    else:
        # Create new vote
        vote = Vote(
            user_id=current_user.id,
            video_id=video.id,
            direction=new_direction,
        )
        db.add(vote)
        
        # If like, add to liked videos (check if already exists first)
        if new_direction == VoteDirection.LIKE:
            existing_liked_result = await db.execute(
                select(UserLikedVideo).where(
                    UserLikedVideo.user_id == current_user.id,
                    UserLikedVideo.video_id == video.id,
                )
            )
            if not existing_liked_result.scalar_one_or_none():
                liked_video = UserLikedVideo(
                    user_id=current_user.id,
                    video_id=video.id,
                )
                db.add(liked_video)
    
    try:
        await db.commit()
    except IntegrityError as e:
        # Handle duplicate key error for user_liked_videos (race condition)
        await db.rollback()
        # Check if it's a duplicate key error for user_liked_videos
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "user_liked_videos_user_id_video_id_key" in error_str:
            # This is fine - the entry already exists, just commit the vote update
            # Re-apply the vote changes
            if existing_vote:
                # Re-fetch and update the existing vote
                existing_vote_result = await db.execute(
                    select(Vote).where(
                        Vote.user_id == current_user.id,
                        Vote.video_id == video.id,
                    )
                )
                existing_vote = existing_vote_result.scalar_one_or_none()
                if existing_vote:
                    existing_vote.direction = new_direction
            else:
                # Re-add the new vote
                vote = Vote(
                    user_id=current_user.id,
                    video_id=video.id,
                    direction=new_direction,
                )
                db.add(vote)
            await db.commit()
        else:
            # Re-raise if it's a different integrity error
            raise
    
    return VoteResponse(
        message="Vote recorded",
        video_id=video_id,
        direction=vote_data.direction,
    )


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Delete own video (comprehensive deletion: DB, storage, cache)"""
    # Check if video exists and user has permission
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    if video.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this video",
        )
    
    # Use deletion service for comprehensive deletion
    try:
        deletion_result = await video_deletion_service.delete_video(str(video.id), db, video)
        
        if not deletion_result.get("database_deleted"):
            error_details = deletion_result.get("errors", [])
            error_message = ', '.join(error_details) if error_details else "Unknown error during deletion"
            logger.error(f"Video deletion failed: {error_message}. Video ID: {video_id}")
            # Raise HTTPException - this will trigger get_db to rollback
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete video: {error_message}",
            )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404, 403 from above) - will trigger rollback
        raise
    except Exception as e:
        # Catch any unexpected errors - will trigger rollback via get_db
        logger.error(f"Unexpected error during video deletion for {video_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
    
    return {
        "message": "Video deleted successfully",
        "video_id": video_id,
        "details": {
            "storage_deleted": deletion_result.get("storage_deleted"),
            "reports_handled": deletion_result.get("reports_handled"),
        }
    }


@router.post("/{video_id}/view", response_model=ViewResponse)
async def record_view(
    video_id: str,
    view_data: ViewRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record video view/watch time"""
    # Check if video exists
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    
    # Create or update view
    if current_user:
        existing_view = await db.execute(
            select(View).where(
                View.video_id == video.id,
                View.user_id == current_user.id,
            )
        )
        view = existing_view.scalar_one_or_none()
        
        if view:
            view.watched_seconds = max(view.watched_seconds, view_data.watched_seconds)
        else:
            view = View(
                video_id=video.id,
                user_id=current_user.id,
                watched_seconds=view_data.watched_seconds,
            )
            db.add(view)
    else:
        # Anonymous view
        view = View(
            video_id=video.id,
            user_id=None,
            watched_seconds=view_data.watched_seconds,
        )
        db.add(view)
    
    await db.commit()
    
    return ViewResponse(message="View recorded")

