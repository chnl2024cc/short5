"""
Diagnostic script to check video processing pipeline
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.celery_app import celery_app
import redis


async def check_database():
    """Check database connection and video statuses"""
    print("=" * 60)
    print("1. DATABASE CHECK")
    print("=" * 60)
    
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Check connection
            result = await session.execute(text("SELECT 1"))
            print("✓ Database connection: OK")
            
            # Check videos by status
            for status in VideoStatus:
                count_result = await session.execute(
                    select(Video).where(Video.status == status)
                )
                count = len(count_result.scalars().all())
                print(f"  {status.value}: {count} videos")
            
            # Check recent processing videos
            recent_result = await session.execute(
                select(Video)
                .where(Video.status == VideoStatus.PROCESSING)
                .order_by(Video.created_at.desc())
                .limit(5)
            )
            recent_videos = recent_result.scalars().all()
            
            if recent_videos:
                print(f"\n  Recent videos stuck in PROCESSING:")
                for video in recent_videos:
                    print(f"    - {video.id} (created: {video.created_at})")
                    if video.error_reason:
                        print(f"      Error: {video.error_reason}")
            else:
                print("\n  No videos currently in PROCESSING status")
        
        await engine.dispose()
        return True
    except Exception as e:
        print(f"✗ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_redis():
    """Check Redis connection and queue status"""
    print("\n" + "=" * 60)
    print("2. REDIS CHECK")
    print("=" * 60)
    
    try:
        # Parse Redis URL
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
            print(f"✓ Redis connection: OK (host={host}, port={port}, db={db})")
            
            # Check queue length
            queue_length = r.llen("celery")
            print(f"  Queue 'celery' length: {queue_length} tasks")
            
            if queue_length > 0:
                print(f"  ⚠ Warning: {queue_length} tasks waiting in queue")
                # Show first few tasks
                tasks = r.lrange("celery", 0, min(4, queue_length - 1))
                print(f"  First {len(tasks)} task(s) in queue")
            
            return True
    except Exception as e:
        print(f"✗ Redis check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_celery_config():
    """Check Celery configuration"""
    print("\n" + "=" * 60)
    print("3. CELERY CONFIGURATION CHECK")
    print("=" * 60)
    
    try:
        print(f"✓ Celery app name: {celery_app.main}")
        print(f"✓ Broker URL: {celery_app.conf.broker_url}")
        print(f"✓ Result backend: {celery_app.conf.result_backend}")
        print(f"✓ Task serializer: {celery_app.conf.task_serializer}")
        print(f"✓ Accept content: {celery_app.conf.accept_content}")
        
        # Check task routes
        if hasattr(celery_app.conf, 'task_routes'):
            print(f"✓ Task routes: {celery_app.conf.task_routes}")
        
        return True
    except Exception as e:
        print(f"✗ Celery config check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_task_sending():
    """Test sending a task to the queue"""
    print("\n" + "=" * 60)
    print("4. TASK SENDING TEST")
    print("=" * 60)
    
    try:
        # Try to send a test task (this will fail if worker isn't running, but we can see if it reaches Redis)
        result = celery_app.send_task(
            "process_video",
            args=["test-video-id", "/app/uploads/test.mp4"],
            queue="celery",
        )
        print(f"✓ Task sent successfully")
        print(f"  Task ID: {result.id}")
        print(f"  Task name: process_video")
        print(f"  Queue: celery")
        print(f"\n  Note: This is a test task. Check video_worker logs to see if it's received.")
        return True
    except Exception as e:
        print(f"✗ Task sending failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_file_paths():
    """Check file paths and permissions"""
    import os
    
    print("\n" + "=" * 60)
    print("5. FILE PATHS CHECK")
    print("=" * 60)
    
    try:
        upload_dir = Path("/app/uploads")
        if upload_dir.exists():
            print(f"✓ Upload directory exists: {upload_dir}")
            print(f"  Absolute path: {upload_dir.absolute()}")
            print(f"  Is directory: {upload_dir.is_dir()}")
            print(f"  Is writable: {os.access(upload_dir, os.W_OK)}")
            
            # Count files
            files = list(upload_dir.glob("*"))
            video_files = [f for f in files if f.suffix.lower() in ['.mp4', '.mov', '.avi']]
            print(f"  Total files: {len(files)}")
            print(f"  Video files: {len(video_files)}")
            
            if video_files:
                print(f"\n  Sample video files:")
                for f in video_files[:5]:
                    print(f"    - {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
        else:
            print(f"✗ Upload directory does not exist: {upload_dir}")
            print(f"  Attempting to create...")
            upload_dir.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created upload directory")
        
        return True
    except Exception as e:
        print(f"✗ File paths check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all diagnostic checks"""
    print("\n" + "=" * 60)
    print("VIDEO PROCESSING PIPELINE DIAGNOSTICS")
    print("=" * 60)
    print()
    
    import os
    
    results = []
    
    # Run checks
    results.append(("Database", await check_database()))
    results.append(("Redis", check_redis()))
    results.append(("Celery Config", check_celery_config()))
    results.append(("File Paths", check_file_paths()))
    results.append(("Task Sending", await test_task_sending()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ All checks passed!")
        print("\nIf videos are still not processing, check:")
        print("  1. Video worker container is running: docker-compose ps video_worker")
        print("  2. Video worker logs: docker-compose logs -f video_worker")
        print("  3. Backend logs: docker-compose logs -f backend")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
