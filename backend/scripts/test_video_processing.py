"""
Test script to verify video processing pipeline
Run: docker-compose exec backend python scripts/test_video_processing.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.video import Video, VideoStatus
from app.celery_app import celery_app

# Try to import redis, fallback if not available
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    print("Warning: redis package not installed, some checks will be skipped")


async def test_video_processing():
    """Test the video processing pipeline"""
    print("=" * 60)
    print("Video Processing Pipeline Test")
    print("=" * 60)
    
    # 1. Check Redis connection
    print("\n1. Checking Redis connection...")
    try:
        r = redis.Redis.from_url("redis://redis:6379/0")
        r.ping()
        print("   ✓ Redis connected")
    except Exception as e:
        print(f"   ✗ Redis connection failed: {e}")
        return
    
    # 2. Check if video_worker is registered
    print("\n2. Checking video_worker registration...")
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()
        
        if stats:
            print(f"   ✓ Found {len(stats)} active worker(s):")
            for worker_name in stats.keys():
                print(f"     - {worker_name}")
        else:
            print("   ⚠ No active workers found")
            print("     Make sure video_worker is running: docker-compose up -d video_worker")
    except Exception as e:
        print(f"   ⚠ Could not check workers: {e}")
    
    # 3. Find stuck videos
    print("\n3. Checking for stuck videos...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video).where(Video.status == VideoStatus.PROCESSING)
        )
        stuck_videos = result.scalars().all()
        
        if stuck_videos:
            print(f"   Found {len(stuck_videos)} video(s) stuck in processing:")
            for video in stuck_videos:
                print(f"     - {video.id}: {video.title or 'Untitled'}")
                print(f"       Created: {video.created_at}")
                
                # Check if file exists
                if video.original_filename:
                    file_ext = Path(video.original_filename).suffix
                else:
                    file_ext = ".mp4"
                
                file_path = Path(f"/app/uploads/{video.id}{file_ext}")
                exists = file_path.exists()
                print(f"       File exists: {exists} ({file_path})")
                
                if exists:
                    # Try to send task
                    print(f"       → Sending task to queue...")
                    try:
                        result = celery_app.send_task(
                            "process_video",
                            args=[str(video.id), str(file_path)],
                            queue="celery",
                        )
                        print(f"       ✓ Task sent! Task ID: {result.id}")
                    except Exception as e:
                        print(f"       ✗ Failed to send task: {e}")
        else:
            print("   ✓ No stuck videos found")
    
    # 4. Check queue length
    print("\n4. Checking Redis queue...")
    if r:
        try:
            queue_length = r.llen("celery")
            print(f"   Queue length: {queue_length} task(s)")
            if queue_length > 0:
                print("   → Tasks are waiting in queue")
        except Exception as e:
            print(f"   ⚠ Could not check queue: {e}")
    else:
        print("   ⚠ Redis package not available, skipping queue check")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check video_worker logs: docker-compose logs -f video_worker")
    print("2. If worker is not running: docker-compose up -d video_worker")
    print("3. Watch for task processing in logs")


if __name__ == "__main__":
    asyncio.run(test_video_processing())
