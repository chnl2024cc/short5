"""
Check the result of a failed task
Run: docker-compose exec backend python scripts/check_task_result.py <task_id>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.celery_app import celery_app

def check_task_result(task_id: str):
    """Check the result of a task"""
    print(f"Checking task result for: {task_id}")
    
    try:
        result = celery_app.AsyncResult(task_id)
        print(f"Task state: {result.state}")
        print(f"Task successful: {result.successful()}")
        print(f"Task failed: {result.failed()}")
        
        if result.failed():
            print(f"\nError info:")
            print(f"  Type: {type(result.info)}")
            if isinstance(result.info, Exception):
                import traceback
                print(f"  Exception: {result.info}")
                print(f"  Traceback:")
                traceback.print_exception(type(result.info), result.info, result.info.__traceback__)
            else:
                print(f"  Info: {result.info}")
        
        if result.successful():
            print(f"\nResult: {result.result}")
            
    except Exception as e:
        print(f"Error checking task: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_task_result.py <task_id>")
        print("\nGet task_id from test_task_sending.py output")
        sys.exit(1)
    
    task_id = sys.argv[1]
    check_task_result(task_id)
