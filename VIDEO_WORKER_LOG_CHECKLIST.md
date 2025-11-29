# Video Worker Log Checklist

## What to Look For in `docker-compose logs -f video_worker`

### ✅ Good Signs (Everything Working)

1. **Startup Messages:**
   ```
   celery@... ready
   ```
   or
   ```
   [INFO/MainProcess] Connected to redis://redis:6379/0
   [INFO/MainProcess] celery@... ready
   ```

2. **S3 Configuration:**
   ```
   S3 credentials not provided - will use local file storage (development mode)
   ```
   (This is expected if AWS is not configured)

3. **Task Received:**
   ```
   [INFO/MainProcess] Received task: process_video[...]
   ```

4. **Processing Started:**
   ```
   📹 Starting video processing for {video_id}
      File path: /app/uploads/{video_id}.mp4
   ✓ File found, starting transcoding...
   ```

5. **Transcoding Progress:**
   ```
   → Transcoding to HLS format...
   ✓ HLS transcoding complete
   ```

6. **Thumbnail Creation:**
   ```
   → Creating thumbnail...
   ✓ Thumbnail created
   ```

7. **Storage Upload:**
   ```
   → Uploading to storage...
   📦 Development mode: Using local file storage for videos/{video_id}/playlist.m3u8
   ✓ File stored locally: /app/uploads/processed/... → /uploads/processed/...
   ✓ Upload complete (X segments + playlists + thumbnail)
   ```

8. **Success:**
   ```
   ✓ Video {video_id} processed successfully
     HLS URL: /uploads/processed/...
     Thumbnail: /uploads/processed/...
   ```

### ⚠️ Warning Signs (May Need Attention)

1. **Worker Not Starting:**
   ```
   No worker processes found
   ```
   → Check if video_worker container is running: `docker-compose ps video_worker`

2. **Redis Connection Issues:**
   ```
   Error connecting to redis://redis:6379/0
   ```
   → Check if Redis is running: `docker-compose ps redis`

3. **Database Connection Issues:**
   ```
   ValueError: DATABASE_URL environment variable is required
   ```
   → Check docker-compose.yml environment variables

4. **File Not Found:**
   ```
   ✗ ERROR: Video file not found: /app/uploads/{video_id}.mp4
   ```
   → Check if file exists: `docker-compose exec backend ls -la /app/uploads/`

5. **FFmpeg Errors:**
   ```
   ✗ ERROR in FFmpeg transcoding: ...
   ```
   → Check FFmpeg installation in video_worker container

6. **Upload Errors:**
   ```
   ✗ ERROR in local file storage: ...
   ```
   → Check permissions on /app/uploads/processed directory

7. **Task Not Received:**
   ```
   (No task received messages)
   ```
   → Check if tasks are being sent from backend
   → Check Redis queue: `docker-compose exec redis redis-cli LLEN celery`

### 🔍 Diagnostic Commands

If you see errors, run these to diagnose:

1. **Check if worker is running:**
   ```bash
   docker-compose ps video_worker
   ```

2. **Check worker logs (last 100 lines):**
   ```bash
   docker-compose logs --tail=100 video_worker
   ```

3. **Check if Redis is accessible:**
   ```bash
   docker-compose exec video_worker python -c "import redis; r=redis.Redis.from_url('redis://redis:6379/0'); print('Connected:', r.ping())"
   ```

4. **Check if database is accessible:**
   ```bash
   docker-compose exec video_worker python -c "import os; from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+psycopg2://')); print('Connected:', engine.connect())"
   ```

5. **Check if files exist:**
   ```bash
   docker-compose exec backend ls -la /app/uploads/
   docker-compose exec video_worker ls -la /app/uploads/
   ```

6. **Check Redis queue:**
   ```bash
   docker-compose exec redis redis-cli
   > LLEN celery
   > KEYS *
   ```

7. **Check if FFmpeg is installed:**
   ```bash
   docker-compose exec video_worker ffmpeg -version
   ```

## Common Issues and Solutions

### Issue: Worker Not Starting
**Solution:**
```bash
docker-compose restart video_worker
docker-compose logs -f video_worker
```

### Issue: Tasks Not Being Received
**Solution:**
1. Check backend is sending tasks
2. Check Redis connection
3. Verify queue name matches ("celery")
4. Restart both backend and video_worker

### Issue: File Not Found
**Solution:**
1. Verify shared volume `backend_uploads` is mounted
2. Check file exists in backend container
3. Verify file path matches what's in database

### Issue: FFmpeg Errors
**Solution:**
1. Check FFmpeg is installed in video_worker Dockerfile
2. Verify video file format is supported
3. Check video file is not corrupted

## Expected Log Flow for Successful Processing

```
[INFO] celery@... ready
[INFO] Received task: process_video[abc-123-def]
📹 Starting video processing for abc-123-def
   File path: /app/uploads/abc-123-def.mp4
✓ File found, starting transcoding...
  → Transcoding to HLS format...
  ✓ HLS transcoding complete
  → Creating thumbnail...
  ✓ Thumbnail created
  → Uploading to storage...
📦 Development mode: Using local file storage for videos/abc-123-def/playlist.m3u8
  ✓ File stored locally: /app/uploads/processed/... → /uploads/processed/...
  ✓ Upload complete (X segments + playlists + thumbnail)
✓ Video abc-123-def processed successfully
  HLS URL: /uploads/processed/...
  Thumbnail: /uploads/processed/...
[INFO] Task process_video[abc-123-def] succeeded
```
