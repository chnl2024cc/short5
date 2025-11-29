# Video Processing Architecture Analysis

## RFC Requirements (Section 80-88)

**Video Worker (FFmpeg):**
- Docker Container, CPU-intensive processing
- Tasks:
  - Transcoding → HLS + mp4
  - Thumbnail + Preview creation
  - Status Update DB → `ready`
- Triggered via Queue (Celery/RQ)
- Video then served via CDN

## Current Implementation Issues

### Problem 1: Two Separate Celery Apps
- **Backend**: Uses `app.celery_app` (named "short_video_platform")
- **Video Worker**: Uses `worker.celery_app` (named "worker")
- Both connect to same Redis, but tasks may not route correctly

### Problem 2: Stub Task in Backend
- `backend/app/tasks/video_processing.py` has a stub task that does nothing
- This creates confusion and potential routing issues

### Problem 3: Task Routing
- Backend sends task with `queue="celery"`
- Video worker listens to default queue
- Need to ensure both use the same queue name

## Correct Architecture (Per RFC)

```
┌─────────────┐         ┌──────────┐         ┌──────────────┐
│   Backend   │────────▶│  Redis   │────────▶│ Video Worker │
│  (FastAPI)  │  Task   │  Queue   │  Task   │   (FFmpeg)   │
└─────────────┘         └──────────┘         └──────────────┘
     │                                            │
     │                                            │
     └───────────────┐      ┌─────────────────────┘
                     │      │
                     ▼      ▼
              ┌─────────────────┐
              │   PostgreSQL     │
              │   (Database)     │
              └─────────────────┘
```

**Flow:**
1. User uploads video → Backend saves file → Creates DB record (status: `uploading`)
2. Backend sends Celery task to Redis queue
3. Video Worker picks up task from queue
4. Video Worker processes video (HLS + thumbnail)
5. Video Worker updates DB (status: `ready`, sets `url_hls`, `thumbnail`)
6. Frontend can now display processed video

## Solution

### Option A: Unified Celery App (Recommended)
- Both backend and video_worker import from a shared Celery app module
- Single source of truth for task definitions
- Cleaner architecture

### Option B: Separate Apps with Proper Routing (Current)
- Keep separate apps but ensure proper task routing
- Backend sends tasks, video_worker receives them
- Both use same Redis broker and queue name

## Recommended Fix

Since we already have separate apps, let's ensure:
1. Both apps use same Redis broker ✅ (already done)
2. Both use same queue name ✅ (using "celery")
3. Task name matches exactly ✅ ("process_video")
4. Video worker is running and listening ✅ (needs verification)
5. File paths are accessible ✅ (shared volume)

The main issue is likely that tasks aren't being received or there's an error during processing.
