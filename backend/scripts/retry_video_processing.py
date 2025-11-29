"""
Script to manually retry processing stuck videos
Run with: docker-compose exec backend python scripts/retry_video_processing.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.video import Video, VideoStatus
from app.celery_app import celery_app


async def retry_stuck_videos():
    """Find videos stuck in processing and retry them"""
    async with AsyncSessionLocal() as db:
        # Find videos stuck in processing
        result = await db.execute(
            select(Video).where(Video.status == VideoStatus.PROCESSING)
        )
        stuck_videos = result.scalars().all()
        
        if not stuck_videos:
            print("No videos stuck in processing status.")
            return
        
        print(f"Found {len(stuck_videos)} video(s) stuck in processing:")
        
        for video in stuck_videos:
            print(f"\nVideo ID: {video.id}")
            print(f"  Title: {video.title or 'Untitled'}")
            print(f"  Status: {video.status.value}")
            print(f"  Created: {video.created_at}")
            
            # Construct file path
            if video.original_filename:
                file_ext = Path(video.original_filename).suffix
            else:
                file_ext = ".mp4"  # Default
            
            file_path = Path(f"/app/uploads/{video.id}{file_ext}")
            
            # Check if file exists
            if file_path.exists():
                print(f"  File exists: {file_path}")
                
                # Retry processing
                try:
                    celery_app.send_task(
                        "process_video",
                        args=[str(video.id), str(file_path)],
                        queue="celery",
                    )
                    print(f"  ✓ Task sent to queue")
                except Exception as e:
                    print(f"  ✗ Failed to send task: {e}")
            else:
                print(f"  ✗ File not found: {file_path}")
                print(f"    Updating status to 'failed'")
                video.status = VideoStatus.FAILED
                await db.commit()


if __name__ == "__main__":
    asyncio.run(retry_stuck_videos())
