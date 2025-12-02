"""
Script to fix video processing for a specific video
Usage: python scripts/fix_video_processing.py <video_id>
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.celery_app import celery_app


async def fix_video_processing(video_id: str):
    """Fix processing for a specific video"""
    print("=" * 60)
    print(f"FIXING VIDEO PROCESSING: {video_id}")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video).where(Video.id == video_id)
        )
        video = result.scalar_one_or_none()
        
        if not video:
            print(f"✗ Video not found: {video_id}")
            return
        
        print(f"\n✓ Video found: {video.title or 'Untitled'}")
        print(f"  Current status: {video.status.value}")
        
        # Determine file path
        if video.original_filename:
            file_ext = Path(video.original_filename).suffix
        else:
            file_ext = ".mp4"  # Default
        
        file_path = Path(f"/app/uploads/originals/{video.id}{file_ext}")
        
        # Check if file exists
        if not file_path.exists():
            print(f"\n✗ File not found: {file_path}")
            print("  → Cannot process video without file")
            print("  → Updating status to FAILED")
            video.status = VideoStatus.FAILED
            video.error_reason = "Video file not found on server"
            await db.commit()
            return
        
        print(f"\n✓ File found: {file_path}")
        print(f"  File size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Reset status to PROCESSING
        if video.status != VideoStatus.PROCESSING:
            print(f"\n  → Resetting status from {video.status.value} to PROCESSING")
            video.status = VideoStatus.PROCESSING
            video.error_reason = None
            await db.commit()
        
        # Send task to queue
        print(f"\n  → Sending processing task to queue...")
        try:
            result = celery_app.send_task(
                "process_video",
                args=[str(video.id), str(file_path)],
                queue="celery",
            )
            print(f"✓ Task sent successfully")
            print(f"  Task ID: {result.id}")
            print(f"  Queue: celery")
            print(f"\n  → Check video_worker logs to see processing:")
            print(f"     docker-compose logs -f video_worker")
        except Exception as e:
            print(f"✗ Failed to send task: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n" + "=" * 60)
        print("NEXT STEPS")
        print("=" * 60)
        print("1. Check if video_worker is running:")
        print("   docker-compose ps video_worker")
        print("\n2. Watch video_worker logs:")
        print("   docker-compose logs -f video_worker")
        print("\n3. Check video status:")
        print(f"   curl {settings.BACKEND_BASE_URL}/api/v1/videos/{video_id}")
        print("\n4. If worker is not running, start it:")
        print("   docker-compose up -d video_worker")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/fix_video_processing.py <video_id>")
        sys.exit(1)
    
    video_id = sys.argv[1]
    asyncio.run(fix_video_processing(video_id))
