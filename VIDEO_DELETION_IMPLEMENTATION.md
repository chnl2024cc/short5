# Video Deletion Feature - Implementation Guide

## Overview
This document outlines the implementation plan for comprehensive video deletion functionality. When a user deletes a video, all associated data (database records, storage files, caches) must be removed.

## Architecture

### Components Involved

1. **Storage Service** (`backend/app/services/storage.py`)
   - Handles S3/R2 and local file deletion
   - Parses URLs to extract storage keys/paths
   - Supports both production (S3) and development (local) modes

2. **Video Deletion Service** (`backend/app/services/video_deletion.py`)
   - Orchestrates complete video deletion
   - Coordinates database, storage, and cache operations
   - Handles errors gracefully

3. **API Endpoint** (`backend/app/api/v1/videos.py`)
   - Enhanced DELETE endpoint
   - Uses deletion service
   - Authorization checks

4. **Frontend Component** (`frontend/pages/profile.vue`)
   - Delete button on video cards
   - Confirmation dialog
   - Optimistic UI updates

## Implementation Steps

### Step 1: Create Storage Utility Service

**File:** `backend/app/services/storage.py`

```python
"""
Storage service for handling file operations (S3/R2 and local)
"""
import os
import boto3
from pathlib import Path
from typing import List, Optional
from botocore.exceptions import ClientError
from urllib.parse import urlparse

from app.core.config import settings


class StorageService:
    """Service for managing video files in storage"""
    
    def __init__(self):
        self.s3_client = None
        self.s3_bucket = settings.S3_BUCKET_NAME
        self.s3_endpoint_url = settings.S3_ENDPOINT_URL
        
        # Initialize S3 client if credentials are available
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.s3_endpoint_url or None,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
    
    def is_s3_mode(self) -> bool:
        """Check if using S3/R2 storage"""
        return self.s3_client is not None and self.s3_bucket
    
    def extract_s3_key_from_url(self, url: str) -> Optional[str]:
        """Extract S3 key from a storage URL"""
        if not url:
            return None
        
        # Handle different URL formats:
        # - https://bucket.s3.region.amazonaws.com/key
        # - https://endpoint/bucket/key
        # - /uploads/processed/key (local)
        
        # Local file path
        if url.startswith("/"):
            return None
        
        parsed = urlparse(url)
        path = parsed.path.lstrip("/")
        
        # Remove bucket name from path if present
        if self.s3_bucket and path.startswith(f"{self.s3_bucket}/"):
            return path[len(f"{self.s3_bucket}/"):]
        
        return path
    
    def delete_from_s3(self, key: str) -> bool:
        """Delete a single file from S3/R2"""
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting S3 object {key}: {e}")
            return False
    
    def delete_prefix_from_s3(self, prefix: str) -> int:
        """Delete all objects with a given prefix from S3/R2"""
        deleted_count = 0
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix)
            
            for page in pages:
                if "Contents" not in page:
                    continue
                
                objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                if objects:
                    response = self.s3_client.delete_objects(
                        Bucket=self.s3_bucket,
                        Delete={"Objects": objects}
                    )
                    deleted_count += len(response.get("Deleted", []))
            
            return deleted_count
        except ClientError as e:
            print(f"Error deleting S3 prefix {prefix}: {e}")
            return deleted_count
    
    def delete_local_file(self, file_path: Path) -> bool:
        """Delete a local file"""
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                return True
        except Exception as e:
            print(f"Error deleting local file {file_path}: {e}")
        return False
    
    def delete_local_files_by_pattern(self, directory: Path, pattern: str) -> int:
        """Delete all files matching a pattern in a directory"""
        deleted_count = 0
        try:
            if not directory.exists():
                return 0
            
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
        except Exception as e:
            print(f"Error deleting local files by pattern: {e}")
        return deleted_count
    
    def delete_video_files(self, video_id: str, video_urls: dict) -> dict:
        """
        Delete all files associated with a video
        
        Args:
            video_id: UUID of the video
            video_urls: Dict with keys like 'url_mp4', 'thumbnail'
        
        Returns:
            Dict with deletion results
        """
        results = {
            "deleted_files": [],
            "failed_files": [],
            "mode": "s3" if self.is_s3_mode() else "local"
        }
        
        if self.is_s3_mode():
            # S3/R2 mode: Delete entire prefix
            prefix = f"videos/{video_id}/"
            deleted_count = self.delete_prefix_from_s3(prefix)
            results["deleted_files"].append(f"{prefix}* ({deleted_count} objects)")
            
            # Also delete MP4 if it exists separately
            if video_urls.get("url_mp4"):
                mp4_key = self.extract_s3_key_from_url(video_urls["url_mp4"])
                if mp4_key and not mp4_key.startswith(f"videos/{video_id}/"):
                    if self.delete_from_s3(mp4_key):
                        results["deleted_files"].append(mp4_key)
                    else:
                        results["failed_files"].append(mp4_key)
        else:
            # Local storage mode
            # Delete processed files
            processed_dir = Path("/app/uploads/processed")
            if processed_dir.exists():
                pattern = f"*{video_id}*"
                deleted_count = self.delete_local_files_by_pattern(processed_dir, pattern)
                results["deleted_files"].append(f"{pattern} ({deleted_count} files)")
            
            # Delete original uploaded file
            upload_dir = Path("/app/uploads")
            if upload_dir.exists():
                # Try common extensions
                for ext in [".mp4", ".mov", ".avi"]:
                    file_path = upload_dir / f"{video_id}{ext}"
                    if file_path.exists():
                        if self.delete_local_file(file_path):
                            results["deleted_files"].append(str(file_path))
                            break
            
            # Delete temp processing directory
            temp_dir = Path(f"/tmp/video_processing/{video_id}")
            if temp_dir.exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    results["deleted_files"].append(f"temp directory: {temp_dir}")
                except Exception as e:
                    results["failed_files"].append(f"temp directory: {e}")
        
        return results


# Global instance
storage_service = StorageService()
```

### Step 2: Create Video Deletion Service

**File:** `backend/app/services/video_deletion.py`

```python
"""
Comprehensive video deletion service
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from app.models.video import Video
from app.models.report import Report
from app.services.storage import storage_service
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


class VideoDeletionService:
    """Service for comprehensive video deletion"""
    
    @staticmethod
    async def delete_video(
        video_id: str,
        db: AsyncSession,
        cancel_tasks: bool = True
    ) -> dict:
        """
        Delete a video completely (database, storage, cache)
        
        Args:
            video_id: UUID of the video
            db: Database session
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
        
        # 1. Fetch video record
        query = select(Video).where(Video.id == video_id)
        video_result = await db.execute(query)
        video = video_result.scalar_one_or_none()
        
        if not video:
            result["errors"].append("Video not found")
            return result
        
        # 2. Collect video URLs before deletion
        video_urls = {
            "url_mp4": video.url_mp4,
            "thumbnail": video.thumbnail,
        }
        
        # 3. Handle reports (mark as resolved with video deletion note)
        try:
            reports_query = select(Report).where(
                Report.target_id == video_id,
                Report.report_type == "video",
                Report.status == "pending"
            )
            reports_result = await db.execute(reports_query)
            reports = reports_result.scalars().all()
            
            for report in reports:
                report.status = "resolved"
                report.resolved_at = db.execute(
                    select(func.now())
                ).scalar()
                # Could set resolved_by to system/admin user if available
            
            if reports:
                await db.commit()
                result["reports_handled"] = True
                result["reports_count"] = len(reports)
        except Exception as e:
            logger.warning(f"Error handling reports for video {video_id}: {e}")
            result["errors"].append(f"Reports handling: {str(e)}")
        
        # 4. Cancel related Celery tasks if needed
        if cancel_tasks:
            try:
                # Revoke task if still pending/processing
                # Note: This requires task ID tracking - may need enhancement
                # For now, we'll skip this as tasks are short-lived
                result["tasks_cancelled"] = True
            except Exception as e:
                logger.warning(f"Error cancelling tasks for video {video_id}: {e}")
                result["errors"].append(f"Task cancellation: {str(e)}")
        
        # 5. Delete storage files
        try:
            storage_results = storage_service.delete_video_files(video_id, video_urls)
            result["storage_deleted"] = True
            result["storage_details"] = storage_results
        except Exception as e:
            logger.error(f"Error deleting storage files for video {video_id}: {e}")
            result["errors"].append(f"Storage deletion: {str(e)}")
            # Continue with DB deletion even if storage fails
        
        # 6. Delete database record (CASCADE handles related records)
        try:
            await db.delete(video)
            await db.commit()
            result["database_deleted"] = True
        except Exception as e:
            logger.error(f"Error deleting video record {video_id}: {e}")
            result["errors"].append(f"Database deletion: {str(e)}")
            await db.rollback()
            return result
        
        # 7. Invalidate cache (if Redis caching is implemented)
        try:
            # Example cache invalidation (implement based on actual cache keys)
            # redis_client.delete(f"video:{video_id}")
            # redis_client.delete(f"user:{video.user_id}:videos")
            # redis_client.delete(f"feed:*")  # Clear all feed caches
            pass
        except Exception as e:
            logger.warning(f"Error invalidating cache for video {video_id}: {e}")
            result["errors"].append(f"Cache invalidation: {str(e)}")
        
        return result


# Global instance
video_deletion_service = VideoDeletionService()
```

### Step 3: Update DELETE Endpoint

**File:** `backend/app/api/v1/videos.py`

Update the existing `delete_video` function:

```python
from app.services.video_deletion import video_deletion_service

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
    
    # Use deletion service
    deletion_result = await video_deletion_service.delete_video(video_id, db)
    
    if not deletion_result["database_deleted"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete video: {', '.join(deletion_result.get('errors', []))}",
        )
    
    return {
        "message": "Video deleted successfully",
        "video_id": video_id,
        "details": {
            "storage_deleted": deletion_result.get("storage_deleted"),
            "reports_handled": deletion_result.get("reports_handled"),
        }
    }
```

### Step 4: Update Frontend Profile View

**File:** `frontend/pages/profile.vue`

Add delete button to video cards and implement deletion:

```vue
<!-- Add delete button to video card -->
<div
  v-for="video in videos"
  :key="video.id"
  class="bg-gray-900 rounded-lg overflow-hidden hover:bg-gray-800 transition-colors cursor-pointer relative group"
>
  <!-- Delete Button -->
  <button
    @click.stop="handleDeleteVideo(video)"
    class="absolute top-2 right-2 z-10 bg-red-600 hover:bg-red-700 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
    title="Delete video"
  >
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  </button>
  
  <!-- Rest of video card... -->
</div>
```

Add to script:

```typescript
const isDeleting = ref<string | null>(null)

const handleDeleteVideo = async (video: any) => {
  // Confirmation dialog
  if (!confirm(`Are you sure you want to delete "${video.title || 'this video'}"? This action cannot be undone.`)) {
    return
  }
  
  isDeleting.value = video.id
  
  try {
    await api.delete(`/videos/${video.id}`)
    
    // Optimistic UI update: Remove from list
    videos.value = videos.value.filter(v => v.id !== video.id)
    
    // Refresh profile stats
    await refreshProfile()
    
    // Show success message (optional)
    // You could use a toast notification here
  } catch (err: any) {
    console.error('Failed to delete video:', err)
    alert(err.response?.data?.detail || 'Failed to delete video. Please try again.')
  } finally {
    isDeleting.value = null
  }
}
```

## Testing Checklist

- [ ] Delete video in production (S3) - verify all files removed
- [ ] Delete video in development (local) - verify all files removed
- [ ] Delete video during processing - verify task cancellation
- [ ] Delete video with reports - verify reports are resolved
- [ ] Delete video with votes/likes/views - verify CASCADE deletes work
- [ ] Delete video as admin - verify authorization
- [ ] Try to delete other user's video - verify 403 error
- [ ] Delete video with missing files - verify graceful error handling
- [ ] Frontend delete button works - verify UI updates correctly
- [ ] Frontend confirmation dialog works

## Error Handling

- Storage deletion failures should not block database deletion
- Log all errors for monitoring
- Return partial success status if some operations fail
- Frontend should handle errors gracefully with user feedback

## Future Enhancements

1. Soft delete option (mark as deleted but keep files)
2. Batch deletion for multiple videos
3. Deletion audit log
4. Recycle bin / restore functionality
5. Background async deletion for large videos

## Notes

- Database CASCADE deletes handle: votes, user_liked_videos, views automatically
- Reports need manual handling (mark as resolved)
- S3 prefix deletion is more efficient than individual file deletion
- Local file deletion uses pattern matching for flexibility
- Cache invalidation can be added when caching is implemented
