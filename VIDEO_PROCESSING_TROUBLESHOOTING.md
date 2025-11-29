# Video Processing Troubleshooting Guide

## Issue: Videos Not Processing After Upload

If videos remain in "processing" status and never complete, follow these diagnostic steps:

## Quick Checks

### 1. Verify Services Are Running
```bash
docker-compose ps
```

All services should be "Up":
- ✅ postgres
- ✅ redis
- ✅ backend
- ✅ video_worker (most important!)
- ✅ frontend (optional)

### 2. Check Video Worker Logs
```bash
docker-compose logs -f video_worker
```

**What to look for:**
- ✅ `celery@... ready` - Worker is running
- ✅ `VIDEO WORKER STARTUP` - Worker initialized correctly
- ✅ `📹 Starting video processing for {video_id}` - Task received
- ❌ Any error messages

### 3. Check Backend Logs
```bash
docker-compose logs -f backend
```

**What to look for:**
- ✅ `Video upload accepted, processing started` - Upload successful
- ❌ Any error messages when sending tasks

### 4. Run Diagnostic Script
```bash
docker-compose exec backend python scripts/diagnose_video_processing.py
```

This will check:
- Database connection and video statuses
- Redis connection and queue status
- Celery configuration
- File paths and permissions
- Task sending capability

## Common Issues and Fixes

### Issue 1: Video Worker Not Running
**Symptoms:**
- Videos stuck in "processing"
- No logs from video_worker
- `docker-compose ps` shows video_worker as "Exited"

**Fix:**
```bash
# Restart video worker
docker-compose restart video_worker

# Check logs for errors
docker-compose logs video_worker

# If it keeps crashing, rebuild
docker-compose build video_worker
docker-compose up -d video_worker
```

### Issue 2: Tasks Not Reaching Worker
**Symptoms:**
- Backend sends tasks successfully
- Worker logs show no task received
- Redis queue has tasks but worker doesn't process them

**Possible Causes:**
1. **Queue name mismatch**
   - Backend sends to queue "celery"
   - Worker must listen to queue "celery"
   - **Fix:** Worker command should include `-Q celery`

2. **Task name mismatch**
   - Backend sends task named "process_video"
   - Worker defines task with `@celery_app.task(name="process_video")`
   - **Fix:** Ensure names match exactly

3. **Redis connection issue**
   - Worker can't connect to Redis
   - **Fix:** Check `CELERY_BROKER_URL` environment variable

**Diagnosis:**
```bash
# Check if tasks are in Redis queue
docker-compose exec redis redis-cli LLEN celery

# If > 0, tasks are waiting but not being processed
# Check worker logs for connection errors
```

### Issue 3: File Not Found
**Symptoms:**
- Worker receives task but fails immediately
- Error: "Video file not found"
- File path issues in logs

**Possible Causes:**
1. **Path mismatch**
   - Backend saves to `/app/uploads/{video_id}.{ext}`
   - Worker looks for same path
   - **Fix:** Both use absolute paths, share `backend_uploads` volume

2. **Volume not mounted**
   - Worker can't access files
   - **Fix:** Check docker-compose.yml has `backend_uploads` volume

**Diagnosis:**
```bash
# Check if file exists in backend container
docker-compose exec backend ls -la /app/uploads/

# Check if file exists in worker container
docker-compose exec video_worker ls -la /app/uploads/

# Both should show the same files
```

### Issue 4: FFmpeg Not Available
**Symptoms:**
- Worker receives task
- Error: "ffmpeg: command not found"
- Transcoding fails

**Fix:**
```bash
# Check if FFmpeg is installed in worker
docker-compose exec video_worker ffmpeg -version

# If not, rebuild worker image
docker-compose build video_worker
docker-compose up -d video_worker
```

### Issue 5: Database Connection Issue
**Symptoms:**
- Worker receives task
- Error updating database
- Status never changes

**Fix:**
```bash
# Check database connection from worker
docker-compose exec video_worker python -c "
import os
from sqlalchemy import create_engine, text
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection: OK')
"
```

### Issue 6: Processing Takes Too Long
**Symptoms:**
- Task starts but never completes
- No error, just hangs

**Possible Causes:**
1. **Large file size**
   - Processing takes longer than timeout
   - **Fix:** Increase `task_time_limit` in worker.py

2. **Insufficient resources**
   - CPU/memory constraints
   - **Fix:** Increase Docker resources or reduce concurrency

**Diagnosis:**
```bash
# Check worker resource usage
docker stats short5_video_worker

# Check if task is still running
docker-compose exec redis redis-cli KEYS "celery-task-meta-*"
```

## Step-by-Step Debugging

### Step 1: Verify Basic Setup
```bash
# 1. All services running
docker-compose ps

# 2. Worker is listening
docker-compose logs video_worker | grep "ready"

# 3. Redis is accessible
docker-compose exec redis redis-cli ping
```

### Step 2: Test Task Sending
```bash
# Run diagnostic script
docker-compose exec backend python scripts/diagnose_video_processing.py

# Or manually send a test task
docker-compose exec backend python -c "
from app.celery_app import celery_app
result = celery_app.send_task('process_video', args=['test-id', '/app/uploads/test.mp4'], queue='celery')
print(f'Task sent: {result.id}')
"
```

### Step 3: Monitor Task Processing
```bash
# Watch worker logs in real-time
docker-compose logs -f video_worker

# In another terminal, upload a video
# You should see task received and processing logs
```

### Step 4: Check for Errors
```bash
# Check all logs for errors
docker-compose logs | grep -i error

# Check specific service
docker-compose logs video_worker | grep -i error
docker-compose logs backend | grep -i error
```

## Manual Recovery

### Retry Stuck Videos
```bash
# Retry videos stuck in processing
docker-compose exec backend python scripts/retry_video_processing.py
```

### Reset Video Status
```sql
-- Connect to database
docker-compose exec postgres psql -U short5_user -d short5_db

-- Reset stuck videos to failed
UPDATE videos SET status = 'failed', error_reason = 'Manual reset - processing timeout' 
WHERE status = 'processing' AND created_at < NOW() - INTERVAL '1 hour';
```

## Prevention

1. **Monitor worker health**
   - Set up health checks
   - Alert on worker failures

2. **Resource monitoring**
   - Monitor CPU/memory usage
   - Scale workers if needed

3. **Error tracking**
   - Log all errors
   - Track processing success rate

4. **Queue monitoring**
   - Alert if queue length > threshold
   - Monitor processing time

## Still Not Working?

1. **Collect diagnostic information:**
   ```bash
   docker-compose logs > logs.txt
   docker-compose ps > services.txt
   docker-compose exec backend python scripts/diagnose_video_processing.py > diagnostics.txt
   ```

2. **Check recent changes:**
   - Review git history
   - Check for configuration changes

3. **Restart everything:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Rebuild if needed:**
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```
