# Video Processing Implementation (Per RFC)

## Architecture Overview

According to **RFC Section 80-88**, the video processing architecture is:

```
User Upload → Backend (FastAPI) → Redis Queue → Video Worker (FFmpeg) → Database Update
```

### Components

1. **Backend (FastAPI)**
   - Receives video upload
   - Saves file to `/app/uploads/`
   - Creates DB record (status: `uploading` → `processing`)
   - Sends Celery task to Redis queue

2. **Video Worker (FFmpeg Docker Container)**
   - Listens to Redis queue for `process_video` tasks
   - Processes video: HLS transcoding + thumbnail
   - Updates DB: status → `ready`, sets `url_hls`, `thumbnail`
   - Uploads to S3/R2 (or local storage in dev mode)

3. **Redis Queue**
   - Connects backend and video_worker
   - Both apps use same broker: `redis://redis:6379/0`
   - Queue name: `celery` (default)

## Implementation Details

### Backend Task Sending
- **File**: `backend/app/api/v1/videos.py`
- **Method**: `celery_app.send_task("process_video", args=[video_id, file_path], queue="celery")`
- **No task definition needed** - backend just sends tasks

### Video Worker Task Processing
- **File**: `video_worker/worker.py`
- **Task**: `@celery_app.task(name="process_video")`
- **Function**: `process_video(video_id: str, file_path: str)`
- **Process**:
  1. Verify file exists
  2. Transcode to HLS (720p, 480p)
  3. Create thumbnail
  4. Upload to storage (S3/R2 or local)
  5. Update DB status to `ready`

## Verification Steps

### 1. Check Services Are Running
```bash
docker-compose ps
# Should show: postgres, redis, backend, video_worker, frontend
```

### 2. Check Video Worker Logs
```bash
docker-compose logs -f video_worker
# Should show: "celery@... ready" and task processing
```

### 3. Test Task Sending
```bash
docker-compose exec backend python scripts/test_video_processing.py
```

### 4. Manually Retry Stuck Videos
```bash
docker-compose exec backend python scripts/retry_video_processing.py
```

## Common Issues

### Issue: Videos Stay in "processing"
**Possible causes:**
1. Video worker not running → `docker-compose up -d video_worker`
2. Tasks not reaching worker → Check Redis connection
3. File path incorrect → Check `/app/uploads/` in backend container
4. Processing error → Check video_worker logs for errors

### Issue: Task Not Received
**Check:**
- Both apps use same Redis: `redis://redis:6379/0`
- Both use same queue: `celery`
- Task name matches: `process_video`
- Video worker is running and listening

### Issue: File Not Found
**Check:**
- File exists in backend: `docker-compose exec backend ls -la /app/uploads/`
- Shared volume mounted: `backend_uploads` volume
- File path in task matches actual file location

## Next Steps

1. **Restart services** to apply changes:
   ```bash
   docker-compose restart backend video_worker
   ```

2. **Check video_worker is running**:
   ```bash
   docker-compose logs video_worker
   ```

3. **Test with a new upload** or retry existing videos:
   ```bash
   docker-compose exec backend python scripts/retry_video_processing.py
   ```

4. **Monitor processing**:
   ```bash
   docker-compose logs -f video_worker
   ```
