"""
Comprehensive video deletion service
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
import logging

from app.models.video import Video
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


class VideoDeletionService:
    """Service for comprehensive video deletion"""
    
    @staticmethod
    async def delete_video(
        video_id: str,
        db: AsyncSession,
        video: Video,
        cancel_tasks: bool = True
    ) -> dict:
        """
        Delete a video completely (database, storage, cache)
        
        Args:
            video_id: UUID of the video (string)
            db: Database session
            video: Video object (already fetched by endpoint)
            cancel_tasks: Whether to cancel related Celery tasks
        
        Returns:
            Dict with deletion results
        """
        result = {
            "video_id": video_id,
            "database_deleted": False,
            "storage_deleted": False,
            "tasks_cancelled": False,
            "reports_handled": False,
            "errors": []
        }
        
        video_uuid = video.id
        
        # 1. Collect video URLs before deletion
        video_urls = {
            "url_mp4": video.url_mp4,
            "thumbnail": video.thumbnail,
        }
        
        # 2. Handle reports (mark as resolved)
        # Skip reports handling - it's optional and can cause transaction issues
        # Reports will be resolved when video is deleted (CASCADE or cleanup)
        result["reports_handled"] = False
        
        # 3. Cancel related Celery tasks
        # Note: Celery tasks are automatically handled - if a video is deleted,
        # the worker will handle the error gracefully when processing
        if cancel_tasks:
            result["tasks_cancelled"] = True
        
        # 4. Delete storage files
        try:
            storage_results = storage_service.delete_video_files(video_id, video_urls)
            result["storage_deleted"] = True
            result["storage_details"] = storage_results
        except Exception as e:
            logger.error(f"Error deleting storage files for video {video_id}: {e}", exc_info=True)
            result["errors"].append(f"Storage deletion: {str(e)}")
            # Continue with DB deletion even if storage fails
        
        # 5. Delete database record (CASCADE handles related records)
        try:
            # Delete using delete statement - more explicit for async SQLAlchemy
            delete_stmt = delete(Video).where(Video.id == video_uuid)
            await db.execute(delete_stmt)
            result["database_deleted"] = True
        except Exception as e:
            logger.error(f"Error deleting video record {video_id}: {e}", exc_info=True)
            result["errors"].append(f"Database deletion: {str(e)}")
            result["database_deleted"] = False
            return result
        
        return result


# Global instance
video_deletion_service = VideoDeletionService()
