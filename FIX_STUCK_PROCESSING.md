# Fix Videos Stuck in Processing Status

## Issue: Videos Remain in "Processing" Status

If videos are stuck in processing and never complete, follow these steps:

## Quick Diagnosis

### Step 1: Check if Worker is Running
```bash
docker-compose ps video_worker
```

Should show: `Up` status

### Step 2: Check Worker Logs
```bash
docker-compose logs -f video_worker
```

**Look for:**
- ✅ `celery@... ready` - Worker is running
- ✅ `📹 Starting video processing for {video_id}` - Task received
- ❌ Any error messages
- ❌ `✗ ERROR updating video status` - Database update failed

### Step 3: Check Stuck Videos
```bash
docker-compose exec backend python scripts/check_stuck_videos.py
```

This will show:
- Videos stuck in processing for > 5 minutes
- When they were last updated
- Any error reasons

### Step 4: Check if Tasks Are in Queue
```bash
docker-compose exec redis redis-cli LLEN celery
```

- `0` = No tasks waiting (either processed or not sent)
- `> 0` = Tasks waiting to be processed

## Common Issues and Fixes

### Issue 1: Worker Not Receiving Tasks

**Symptoms:**
- Videos stuck in processing
- No logs in worker showing task received
- Tasks in Redis queue but not processed

**Fix:**
```bash
# Restart worker
docker-compose restart video_worker

# Check worker is listening to correct queue
docker-compose logs video_worker | grep "ready"
# Should show: "celery@... ready"
```

### Issue 2: Database Update Failing

**Symptoms:**
- Worker logs show processing started
- Processing completes but status doesn't change
- Error: `✗ ERROR updating video status`

**Fix Applied:**
- ✅ Fixed UUID handling in `update_video_status` function
- ✅ Added proper error logging
- ✅ Added row count verification

**Restart worker to apply fix:**
```bash
docker-compose restart video_worker
```

### Issue 3: File Not Found

**Symptoms:**
- Worker receives task
- Error: "Video file not found"
- File path issues in logs

**Fix:**
```bash
# Check if file exists in backend
docker-compose exec backend ls -la /app/uploads/

# Check if file exists in worker
docker-compose exec video_worker ls -la /app/uploads/

# Both should show the same files (shared volume)
```

### Issue 4: Processing Error

**Symptoms:**
- Worker receives task
- Processing starts but fails
- Error in worker logs

**Check logs:**
```bash
docker-compose logs video_worker | grep -i error
```

**Common errors:**
- FFmpeg not found → Rebuild worker image
- Invalid video format → Check file
- Out of memory → Increase Docker resources

## Manual Recovery

### Retry Stuck Videos
```bash
# Retry videos stuck in processing
docker-compose exec backend python scripts/retry_video_processing.py
```

### Manually Update Status
```sql
-- Connect to database
docker-compose exec postgres psql -U short5_user -d short5_db

-- Check stuck videos
SELECT id, title, status, created_at, updated_at, error_reason 
FROM videos 
WHERE status = 'processing' 
ORDER BY updated_at DESC;

-- Manually set to failed (if needed)
UPDATE videos 
SET status = 'failed', 
    error_reason = 'Manual reset - processing timeout',
    updated_at = CURRENT_TIMESTAMP
WHERE status = 'processing' 
  AND updated_at < NOW() - INTERVAL '30 minutes';
```

## Step-by-Step Recovery

### 1. Restart Worker (Apply Fixes)
```bash
docker-compose restart video_worker
```

### 2. Check Worker Logs
```bash
docker-compose logs -f video_worker
```

### 3. Upload Test Video
- Upload a new video through frontend
- Watch worker logs for processing
- Check if status changes to READY

### 4. Retry Stuck Videos
```bash
docker-compose exec backend python scripts/retry_video_processing.py
```

### 5. Verify Status Updates
```bash
docker-compose exec backend python scripts/check_stuck_videos.py
```

## Prevention

1. **Monitor worker health:**
   - Set up alerts for worker failures
   - Monitor processing queue length

2. **Resource monitoring:**
   - Ensure sufficient CPU/memory
   - Monitor disk space

3. **Error tracking:**
   - Check worker logs regularly
   - Monitor failed video count

## Recent Fixes Applied

✅ **Fixed UUID handling in database update**
- Proper UUID conversion
- Better error handling
- Row count verification

✅ **Improved logging**
- Better error messages
- Database update confirmation
- File path verification

## Next Steps

1. **Restart worker:**
   ```bash
   docker-compose restart video_worker
   ```

2. **Check logs:**
   ```bash
   docker-compose logs -f video_worker
   ```

3. **Test with new upload:**
   - Upload a video
   - Watch logs
   - Verify status changes to READY

4. **Retry stuck videos:**
   ```bash
   docker-compose exec backend python scripts/retry_video_processing.py
   ```
