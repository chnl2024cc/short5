# Local Storage Only - Simplification Plan

## Overview
Remove all S3/R2 code and use local Docker volumes exclusively for video storage.

## Benefits
- ✅ Simpler codebase (no S3 client, credentials, fallback logic)
- ✅ No external dependencies (boto3 optional)
- ✅ Lower costs (no S3 fees)
- ✅ Faster development (no upload delays)
- ✅ Easier debugging (files directly accessible)
- ✅ Works great for small/medium scale

## Changes Required

### 1. Video Worker (`video_worker/worker.py`)
- Remove S3 client initialization (lines 70-96)
- Simplify `upload_to_s3()` → rename to `store_file()` (always local)
- Remove boto3 import (make optional or remove)

### 2. Backend Storage Service (`backend/app/services/storage.py`)
- Simplify to only handle local file operations
- Remove S3 deletion methods
- Keep local file deletion logic

### 3. Configuration (`backend/app/core/config.py`)
- Make S3 settings optional (can keep for future, but not required)
- Or remove entirely

### 4. Docker Compose
- Remove S3 environment variables (optional - can keep empty)
- Ensure `backend_uploads` volume is properly sized

### 5. Dependencies
- Make `boto3` optional in `requirements.txt` (or remove)

## Storage Structure

```
/app/uploads/
├── {video_id}.mp4              # Original uploaded file
└── processed/
    └── videos/
        └── {video_id}/
            ├── playlist.m3u8   # Master HLS playlist
            ├── thumbnail.jpg
            ├── 720p/
            │   ├── {video_id}.m3u8
            │   └── {video_id}_*.ts  # Video segments
            └── 480p/
                ├── {video_id}.m3u8
                └── {video_id}_*.ts
```

## Volume Management

The `backend_uploads` volume stores all videos. Monitor size:
```bash
docker volume inspect short5_swiper_bugagaa_backend_uploads
```

## Backup Strategy

For production, consider:
1. Regular volume backups
2. rsync to backup server
3. Or add S3 backup script (optional, separate from main storage)

## Migration Path

1. Current videos: Already in local storage (if S3 not configured)
2. No migration needed - just remove S3 code
3. Existing videos continue to work
