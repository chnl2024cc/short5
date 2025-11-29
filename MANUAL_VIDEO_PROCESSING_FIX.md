# Manual Video Processing Fix

## Problem
Videos are stuck in "processing" status because tasks aren't being processed by the video_worker.

## Quick Diagnostic Steps

1. **Check if video_worker is running:**
   ```bash
   docker-compose ps video_worker
   ```

2. **Check video_worker logs:**
   ```bash
   docker-compose logs -f video_worker
   ```

3. **Check if tasks are in Redis queue:**
   ```bash
   docker-compose exec redis redis-cli
   > KEYS *
   > LLEN celery
   ```

4. **Manually trigger processing for stuck videos:**
   ```bash
   docker-compose exec backend python scripts/retry_video_processing.py
   ```

## Common Issues and Fixes

### Issue 1: Video Worker Not Running
**Solution:**
```bash
docker-compose up -d video_worker
docker-compose logs -f video_worker
```

### Issue 2: Tasks Not Routing Between Apps
The backend and video_worker use different Celery app instances. They should share the same Redis broker and queue.

**Verify both are using same Redis:**
```bash
# Check backend
docker-compose exec backend python -c "from app.celery_app import celery_app; print(celery_app.conf.broker_url)"

# Check video_worker  
docker-compose exec video_worker python -c "from worker import celery_app; print(celery_app.conf.broker_url)"
```

Both should show: `redis://redis:6379/0`

### Issue 3: File Path Issues
The video_worker needs access to uploaded files.

**Check if files exist:**
```bash
docker-compose exec backend ls -la /app/uploads/
```

**Check file path in database:**
```bash
docker-compose exec postgres psql -U short5_user -d short5_db -c "SELECT id, status, original_filename FROM videos WHERE status = 'processing' LIMIT 5;"
```

### Issue 4: Manual Retry for Stuck Videos

**Option A: Use the retry script:**
```bash
docker-compose exec backend python scripts/retry_video_processing.py
```

**Option B: Manually update status and retry:**
```bash
# Connect to database
docker-compose exec postgres psql -U short5_user -d short5_db

# Find stuck videos
SELECT id, status, created_at FROM videos WHERE status = 'processing';

# Update a specific video to retry (replace VIDEO_ID)
UPDATE videos SET status = 'uploading' WHERE id = 'VIDEO_ID';

# Or mark as failed
UPDATE videos SET status = 'failed' WHERE id = 'VIDEO_ID';
```

**Option C: Directly trigger task from Python:**
```bash
docker-compose exec backend python
```
```python
from app.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.video import Video
from sqlalchemy import select
import asyncio

async def retry_video():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video).where(Video.status == "processing").limit(1)
        )
        video = result.scalar_one_or_none()
        if video:
            file_path = f"/app/uploads/{video.id}.mp4"
            celery_app.send_task(
                "process_video",
                args=[str(video.id), file_path],
                queue="celery"
            )
            print(f"Sent task for video {video.id}")

asyncio.run(retry_video())
```

## Testing Video Processing

1. **Upload a new test video** - This will create a fresh task
2. **Watch video_worker logs:**
   ```bash
   docker-compose logs -f video_worker
   ```
3. **You should see:**
   - Task received
   - Processing started
   - FFmpeg commands executing
   - Status updates

## If Nothing Works

1. **Restart all services:**
   ```bash
   docker-compose restart
   ```

2. **Rebuild video_worker:**
   ```bash
   docker-compose build video_worker
   docker-compose up -d video_worker
   ```

3. **Check Redis connection:**
   ```bash
   docker-compose exec video_worker python -c "import redis; r=redis.Redis.from_url('redis://redis:6379/0'); print('Connected:', r.ping())"
   ```

4. **Check database connection:**
   ```bash
   docker-compose exec video_worker python -c "import os; from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+psycopg2://')); print('Connected:', engine.connect())"
   ```
