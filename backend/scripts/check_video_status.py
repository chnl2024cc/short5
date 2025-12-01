"""
Script to check status of a specific video
Usage: python scripts/check_video_status.py <video_id>
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
import redis
from app.core.config import settings


async def check_video(video_id: str):
    """Check status of a specific video"""
    print("=" * 60)
    print(f"VIDEO STATUS CHECK: {video_id}")
    print("=" * 60)
    
    # 1. Check database
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video).where(Video.id == video_id)
        )
        video = result.scalar_one_or_none()
        
        if not video:
            print(f"✗ Video not found in database: {video_id}")
            return
        
        print(f"\n✓ Video found in database")
        print(f"  ID: {video.id}")
        print(f"  Title: {video.title or 'Untitled'}")
        print(f"  Status: {video.status.value}")
        print(f"  Created: {video.created_at}")
        print(f"  Updated: {video.updated_at}")
        if video.error_reason:
            print(f"  Error: {video.error_reason}")
        if video.thumbnail:
            print(f"  Thumbnail: {video.thumbnail}")
        
        # Check file
        if video.original_filename:
            file_ext = Path(video.original_filename).suffix
        else:
            file_ext = ".mp4"
        
        file_path = Path(f"/app/uploads/originals/{video.id}{file_ext}")
        print(f"\n  File path: {file_path}")
        print(f"  File exists: {file_path.exists()}")
        if file_path.exists():
            print(f"  File size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 2. Check Redis queue
    print("\n" + "=" * 60)
    print("REDIS QUEUE CHECK")
    print("=" * 60)
    
    try:
        redis_url = settings.CELERY_BROKER_URL
        if redis_url.startswith("redis://"):
            redis_url = redis_url.replace("redis://", "")
            if "/" in redis_url:
                host_port, db = redis_url.split("/")
            else:
                host_port, db = redis_url, "0"
            
            if ":" in host_port:
                host, port = host_port.split(":")
            else:
                host, port = host_port, "6379"
            
            r = redis.Redis(host=host, port=int(port), db=int(db), decode_responses=True)
            r.ping()
            print(f"✓ Redis connected")
            
            queue_length = r.llen("celery")
            print(f"  Queue 'celery' length: {queue_length} tasks")
            
            if queue_length > 0:
                print(f"  ⚠ {queue_length} task(s) waiting in queue")
                # Check if our video is in the queue
                tasks = r.lrange("celery", 0, queue_length - 1)
                video_in_queue = any(video_id in str(task) for task in tasks)
                if video_in_queue:
                    print(f"  ⚠ Video task found in queue")
                else:
                    print(f"  ℹ Video task not in queue (may have been processed or not sent)")
    except Exception as e:
        print(f"✗ Redis check failed: {e}")
    
    # 3. Check if worker is active
    print("\n" + "=" * 60)
    print("WORKER CHECK")
    print("=" * 60)
    
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()
        
        if stats:
            print(f"✓ Found {len(stats)} active worker(s):")
            for worker_name in stats.keys():
                print(f"  - {worker_name}")
        else:
            print("✗ No active workers found")
            print("  → Video worker may not be running")
            print("  → Run: docker-compose up -d video_worker")
    except Exception as e:
        print(f"⚠ Could not check workers: {e}")
        print("  → This is normal if worker is not running")
    
    # 4. Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if video.status == VideoStatus.PROCESSING:
        print("Video is stuck in PROCESSING status.")
        print("\nTry these steps:")
        print("1. Check video_worker logs:")
        print("   docker-compose logs -f video_worker")
        print("\n2. Check if worker is running:")
        print("   docker-compose ps video_worker")
        print("\n3. Retry processing:")
        print("   docker-compose exec backend python scripts/retry_video_processing.py")
        print("\n4. Manually trigger for this video:")
        if file_path.exists():
            print(f"   docker-compose exec backend python -c \"")
            print(f"   from app.celery_app import celery_app;")
            print(f"   celery_app.send_task('process_video', args=['{video_id}', '{file_path}'], queue='celery')\"")
    elif video.status == VideoStatus.FAILED:
        print("Video processing failed.")
        if video.error_reason:
            print(f"Error reason: {video.error_reason}")
        print("\nTo retry:")
        print("   docker-compose exec backend python scripts/retry_video_processing.py")
    elif video.status == VideoStatus.READY:
        print("✓ Video is ready!")
    else:
        print(f"Video status: {video.status.value}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_video_status.py <video_id>")
        sys.exit(1)
    
    video_id = sys.argv[1]
    asyncio.run(check_video(video_id))
