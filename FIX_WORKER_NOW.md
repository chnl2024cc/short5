# URGENT: Fix Video Worker - Apply Local Storage Changes

## Problem
Worker is still using OLD code that tries to use S3. The container needs to be restarted/rebuilt.

## Quick Fix - Run These Commands:

### Step 1: Stop and Rebuild Worker
```bash
docker-compose stop video_worker
docker-compose build video_worker
docker-compose up -d video_worker
```

### Step 2: Verify Worker is Using New Code
```bash
docker-compose logs video_worker | grep -i "local file storage\|S3 client"
```

You should see:
- `📦 S3 credentials not provided - will use local file storage (development mode)`

### Step 3: Check Environment Variables in Container
```bash
docker-compose exec video_worker env | grep -E "AWS_|S3_"
```

Should show empty values:
- `AWS_ACCESS_KEY_ID=`
- `AWS_SECRET_ACCESS_KEY=`
- `S3_BUCKET_NAME=`

### Step 4: Retry Stuck Videos
```bash
docker-compose exec backend python scripts/retry_video_processing.py
```

## Alternative: Full Restart
If the above doesn't work:
```bash
docker-compose down
docker-compose up -d
```

## What Changed
1. ✅ `docker-compose.yml` - Removed default S3_BUCKET_NAME
2. ✅ `video_worker/worker.py` - Added USE_S3 check and local storage fallback
3. ⚠️ **Worker container needs restart to apply changes**

## Verification
After restart, check logs:
```bash
docker-compose logs -f video_worker
```

When processing a video, you should see:
- `📦 Development mode: Using local file storage for videos/...`
- NOT: `📦 Production mode: Uploading ... to S3/R2`
