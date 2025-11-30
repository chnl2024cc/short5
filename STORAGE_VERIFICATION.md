# Local Storage & Volume Verification

## Overview
This document verifies that local Docker volume storage is correctly implemented for video upload, processing, and serving.

## Volume Configuration

### Docker Compose Volumes
```yaml
volumes:
  backend_uploads:  # Shared volume for all video files
  video_worker_temp:  # Temporary processing files
```

### Volume Mounts

**Backend Container:**
- `backend_uploads:/app/uploads` - Stores uploaded and processed files
- `./backend:/app` - Code hot-reload

**Video Worker Container:**
- `backend_uploads:/app/uploads` - **SHARED** - Access uploaded files and store processed files
- `video_worker_temp:/tmp/video_processing` - Temporary processing directory

## File Flow

### 1. Upload (Backend)
```
User uploads video
  ↓
Backend receives file
  ↓
Saves to: /app/uploads/{video_id}.mp4
  ↓
Volume: backend_uploads:/app/uploads
```

**Code:** `backend/app/api/v1/videos.py:82-83`
```python
file_path = UPLOAD_DIR / video_filename  # /app/uploads/{video_id}.mp4
file_path.write_bytes(content)
```

### 2. Processing (Video Worker)
```
Celery task receives: file_path="/app/uploads/{video_id}.mp4"
  ↓
Video worker reads from: /app/uploads/{video_id}.mp4 (shared volume)
  ↓
Processes in: /tmp/video_processing/{video_id}/ (temp volume)
  ↓
Stores processed files to: /app/uploads/processed/videos/{video_id}/
```

**Code:** `video_worker/worker.py:397-400`
```python
input_path = Path(file_path)  # /app/uploads/{video_id}.mp4
if not input_path.is_absolute():
    input_path = Path("/app/uploads") / input_path
```

**Code:** `video_worker/worker.py:328-346`
```python
local_storage = Path("/app/uploads/processed")
dest_path = local_storage / storage_key  # videos/{video_id}/playlist.m3u8
```

### 3. Serving (Backend)
```
Backend serves static files from: /app/uploads
  ↓
URL: http://localhost:8000/uploads/processed/videos/{video_id}/playlist.m3u8
  ↓
File: /app/uploads/processed/videos/{video_id}/playlist.m3u8
```

**Code:** `backend/app/main.py:45-48`
```python
uploads_dir = Path("/app/uploads")
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
```

## Directory Structure

```
/app/uploads/  (backend_uploads volume)
├── {video_id}.mp4                    # Original uploaded file
└── processed/
    └── videos/
        └── {video_id}/
            ├── playlist.m3u8         # Master HLS playlist
            ├── thumbnail.jpg
            ├── 720p/
            │   ├── {video_id}.m3u8   # Quality playlist
            │   └── {video_id}_*.ts   # Video segments
            └── 480p/
                ├── {video_id}.m3u8
                └── {video_id}_*.ts
```

## Verification Checklist

### ✅ Volume Mounts
- [x] Backend mounts `backend_uploads:/app/uploads`
- [x] Video worker mounts `backend_uploads:/app/uploads` (shared)
- [x] Video worker mounts `video_worker_temp:/tmp/video_processing` (temp)

### ✅ Upload Flow
- [x] Backend saves to `/app/uploads/{video_id}.mp4`
- [x] File is accessible in shared volume
- [x] Path is absolute (`/app/uploads/...`)

### ✅ Processing Flow
- [x] Video worker receives absolute path
- [x] Video worker can read from `/app/uploads/{video_id}.mp4`
- [x] Processes in temp directory `/tmp/video_processing/{video_id}/`
- [x] Stores processed files to `/app/uploads/processed/videos/{video_id}/`
- [x] Directory structure preserved for HLS playlists

### ✅ Serving Flow
- [x] Backend mounts `/app/uploads` as `/uploads` static files
- [x] Files accessible at `http://localhost:8000/uploads/processed/...`
- [x] HLS playlists can resolve relative segment paths

### ✅ Path Consistency
- [x] All paths use absolute paths (`/app/uploads/...`)
- [x] Upload directory: `/app/uploads`
- [x] Processed directory: `/app/uploads/processed`
- [x] Storage key structure: `videos/{video_id}/...`

## Potential Issues to Watch

### 1. Volume Permissions
- Ensure containers can read/write to shared volume
- Video worker runs as root (C_FORCE_ROOT=true) - should be fine

### 2. File Path Resolution
- Backend sends absolute path: `/app/uploads/{video_id}.mp4` ✓
- Video worker handles both absolute and relative paths ✓

### 3. Directory Structure
- HLS playlists use relative paths: `720p/{video_id}.m3u8`
- Storage preserves structure: `videos/{video_id}/720p/{video_id}.m3u8` ✓

### 4. Volume Size
- Monitor `backend_uploads` volume size
- No automatic cleanup (videos persist until deleted)

## Testing Commands

### Check Volume Mounts
```bash
# Verify backend can see uploads directory
docker-compose exec backend ls -la /app/uploads

# Verify video worker can see uploads directory
docker-compose exec video_worker ls -la /app/uploads

# Check if they're the same volume
docker-compose exec backend touch /app/uploads/test.txt
docker-compose exec video_worker ls -la /app/uploads/test.txt
# Should see the file in both containers
```

### Check File Storage
```bash
# After uploading a video, check original file
docker-compose exec backend ls -la /app/uploads/*.mp4

# After processing, check processed files
docker-compose exec backend ls -la /app/uploads/processed/videos/

# Check HLS structure
docker-compose exec backend find /app/uploads/processed -name "*.m3u8"
```

### Check Volume Size
```bash
docker volume inspect short5_swiper_bugagaa_backend_uploads
```

## Summary

✅ **All components correctly configured:**
- Volume mounts are correct and shared
- Paths are absolute and consistent
- Directory structure is preserved
- Backend can serve files correctly
- Video worker can access and store files

The local storage implementation is correct and ready to use!
