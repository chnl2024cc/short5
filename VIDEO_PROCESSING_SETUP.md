# Video Processing Setup Guide

## Problem: Videos Stuck in "Processing" Status

If your uploaded videos show "Processing..." and never complete, the video worker is not running or not properly configured.

## Quick Fix: Start the Video Worker

### Option 1: Using Docker Compose (Recommended)

```bash
# Start all services including video_worker
docker-compose up -d

# Check if video_worker is running
docker-compose ps video_worker

# View video_worker logs
docker-compose logs -f video_worker
```

### Option 2: Manual Start (Development)

If you're running services manually:

```bash
# 1. Make sure Redis is running
docker-compose up -d redis

# 2. Start the video_worker container
docker-compose up -d video_worker

# Or run locally (requires FFmpeg installed)
cd video_worker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://short5_user:short5_password@localhost:5432/short5_db"
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# Optional: S3 credentials (if not set, uses local file storage)
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export S3_BUCKET_NAME="your-bucket"

# Start Celery worker
celery -A worker worker --loglevel=info
```

## Development Mode (No S3 Required)

The video worker now supports **development mode** that works without S3 credentials:

- If `AWS_ACCESS_KEY_ID` or `S3_BUCKET_NAME` is not set, videos are processed and stored locally
- Processed files are saved to `/app/uploads/processed/` in the container
- The backend serves these files via `/uploads/` endpoint
- Videos will be accessible at `http://localhost:8000/uploads/processed/...`

## Verify Video Processing is Working

1. **Check if video_worker is running:**
   ```bash
   docker ps | grep video_worker
   ```

2. **Check Redis queue:**
   ```bash
   docker-compose exec redis redis-cli
   > KEYS *
   > LLEN celery
   ```

3. **Check video_worker logs:**
   ```bash
   docker-compose logs -f video_worker
   ```

4. **Check database for video status:**
   ```bash
   docker-compose exec postgres psql -U short5_user -d short5_db
   > SELECT id, status, url_mp4, thumbnail FROM videos ORDER BY created_at DESC LIMIT 5;
   ```

## Troubleshooting

### Issue: "Video file not found"

**Problem:** The video_worker can't find the uploaded file.

**Solution:**
- Ensure `backend_uploads` volume is shared between backend and video_worker
- Check file path in database: `SELECT id, original_filename FROM videos WHERE status = 'processing';`
- Verify file exists: `docker-compose exec backend ls -la /app/uploads/`

### Issue: "Error uploading to S3"

**Problem:** S3 credentials are missing or incorrect.

**Solution:**
- For development: Leave S3 credentials unset (uses local storage)
- For production: Set correct `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `S3_BUCKET_NAME`

### Issue: "FFmpeg not found"

**Problem:** FFmpeg is not installed in the video_worker container.

**Solution:**
- Rebuild the video_worker container: `docker-compose build video_worker`
- Check Dockerfile includes FFmpeg installation

### Issue: Videos stay in "processing" forever

**Problem:** Video worker is not processing tasks.

**Solution:**
1. Check if video_worker is running: `docker-compose ps video_worker`
2. Check logs for errors: `docker-compose logs video_worker`
3. Verify Redis connection: `docker-compose exec video_worker python -c "import redis; r=redis.Redis.from_url('redis://redis:6379/0'); print(r.ping())"`
4. Verify database connection: Check `DATABASE_URL` in video_worker environment

## Processing Existing Videos

If you have videos stuck in "processing" status, you can manually trigger processing:

```python
# In Python shell or script
from app.celery_app import celery_app
from app.core.database import get_db
from app.models.video import Video
from sqlalchemy import select

# Get a stuck video
db = next(get_db())
video = db.execute(select(Video).where(Video.status == "processing")).scalar_one_or_none()

if video:
    # Trigger processing
    celery_app.send_task(
        "process_video",
        args=[str(video.id), f"/app/uploads/{video.id}.mp4"]  # Adjust path as needed
    )
```

Or via SQL:

```sql
-- Find stuck videos
SELECT id, status, created_at FROM videos WHERE status = 'processing';

-- Manually update status to retry (or delete and re-upload)
UPDATE videos SET status = 'failed' WHERE status = 'processing' AND created_at < NOW() - INTERVAL '1 hour';
```

## Production Setup

For production, ensure:

1. **S3/R2 credentials are configured:**
   ```env
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   S3_BUCKET_NAME=your-bucket
   AWS_REGION=us-east-1
   # For Cloudflare R2:
   S3_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
   ```

2. **Video worker is running as a service:**
   - Use systemd, supervisor, or Docker Compose in production
   - Monitor worker health and restart on failure

3. **Resource allocation:**
   - Video processing is CPU-intensive
   - Allocate sufficient CPU and memory to video_worker container
   - Consider scaling workers based on upload volume

## Next Steps

Once the video_worker is running:
1. Upload a new video
2. Check video_worker logs to see processing progress
3. Video status should change from "processing" → "ready"
4. Videos should appear in your profile and feed
