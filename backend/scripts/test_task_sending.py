"""
Test script to verify task sending works
Run: docker-compose exec backend python scripts/test_task_sending.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.celery_app import celery_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_task_sending():
    """Test sending a task to the queue"""
    print("=" * 60)
    print("TESTING TASK SENDING")
    print("=" * 60)
    
    # Test sending task
    test_video_id = "test-video-id-123"
    test_file_path = "/app/uploads/test.mp4"
    
    print(f"\nSending test task:")
    print(f"  Task name: process_video")
    print(f"  Video ID: {test_video_id}")
    print(f"  File path: {test_file_path}")
    print(f"  Queue: celery")
    
    try:
        result = celery_app.send_task(
            "process_video",
            args=[test_video_id, test_file_path],
            queue="celery",
            ignore_result=False,  # Set to False to capture errors
        )
        print(f"\n✓ Task sent successfully!")
        print(f"  Task ID: {result.id}")
        print(f"  Task state: {result.state}")
        
        # Wait a moment and check result
        import time
        print(f"\n  Waiting 2 seconds for task to process...")
        time.sleep(2)
        
        # Check task result
        try:
            task_result = celery_app.AsyncResult(result.id)
            print(f"  Task state after wait: {task_result.state}")
            
            if task_result.failed():
                print(f"\n  ✗ Task failed!")
                print(f"  Error info: {task_result.info}")
                if isinstance(task_result.info, Exception):
                    import traceback
                    print(f"  Exception type: {type(task_result.info)}")
                    print(f"  Exception: {task_result.info}")
                print(f"\n  To see full error details, run:")
                print(f"    docker-compose exec backend python scripts/check_task_result.py {result.id}")
        except Exception as e:
            print(f"  ⚠ Could not check task result: {e}")
        
        # Check if task is in queue
        try:
            import redis
            from app.core.config import settings
            
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
                queue_length = r.llen("celery")
                print(f"\n  Queue 'celery' length: {queue_length} tasks")
                
                if queue_length > 0:
                    print(f"  ⚠ {queue_length} task(s) in queue")
                    print(f"  → Check video_worker logs to see if task is received")
                else:
                    print(f"  → Task may have been processed or not queued")
        except Exception as e:
            print(f"  ⚠ Could not check queue: {e}")
        
        return True
    except Exception as e:
        print(f"\n✗ Failed to send task: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_task_sending()
    sys.exit(0 if success else 1)
