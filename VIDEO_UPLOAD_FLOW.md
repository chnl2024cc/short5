# Video Upload Process Flow

## Complete Service Interaction Diagram

This document visualizes the entire video upload and processing pipeline, showing how services communicate through Redis and Celery.

---

## 🎬 High-Level Flow Overview

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │ 1. POST /api/v1/videos/upload
       │    (multipart/form-data: video file)
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│                  (short5_backend)                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ POST /api/v1/videos/upload                         │    │
│  │ 1. Validate file (size, format)                    │    │
│  │ 2. Create Video record in DB (status: UPLOADING)   │    │
│  │ 3. Save file to /app/uploads/originals/{video_id}  │    │
│  │ 4. Update Video status to PROCESSING               │    │
│  │ 5. Send task to Celery via Redis                   │    │
│  └────────────────────────────────────────────────────┘    │
└──────┬──────────────────────────────────────────────────────┘
       │ 2. celery_app.send_task("process_video", ...)
       │    queue="celery"
       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Redis                                  │
│                  (short5_redis)                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Queue: "celery"                                    │    │
│  │                                                     │    │
│  │ Task Message:                                       │    │
│  │ {                                                   │    │
│  │   "task": "process_video",                         │    │
│  │   "id": "abc-123-def-456",                         │    │
│  │   "args": [                                         │    │
│  │     "video-uuid-here",                             │    │
│  │     "/app/uploads/originals/video-uuid.mp4"        │    │
│  │   ],                                                │    │
│  │   "kwargs": {},                                     │    │
│  │   "queue": "celery"                                 │    │
│  │ }                                                   │    │
│  └────────────────────────────────────────────────────┘    │
└──────┬──────────────────────────────────────────────────────┘
       │ 3. Worker polls queue
       │    (Celery worker subscribes to "celery" queue)
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Video Worker (FFmpeg)                         │
│            (short5_video_worker)                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ @celery_app.task(name="process_video")            │    │
│  │ def process_video(video_id, file_path):            │    │
│  │                                                     │    │
│  │ 1. Receive task from Redis queue                   │    │
│  │ 2. Validate video file                            │    │
│  │ 3. Transcode to MP4                                │    │
│  │ 4. Create thumbnail                                │    │
│  │ 5. Store files in /app/uploads/processed/        │    │
│  │ 6. Update database (status: READY)                │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
       │
       │ 4. Database updates via PostgreSQL
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL                               │
│                 (short5_postgres)                           │
│                                                              │
│  videos table:                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │ id: video-uuid                                     │    │
│  │ status: "ready"                                    │    │
│  │ url_mp4: "/uploads/processed/video-uuid/video.mp4"│    │
│  │ thumbnail: "/uploads/processed/.../thumbnail.jpg" │    │
│  │ duration_seconds: 45                               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Detailed Step-by-Step Process

### **Step 1: User Uploads Video**

**Service:** FastAPI Backend (`short5_backend`)  
**Endpoint:** `POST /api/v1/videos/upload`

**Actions:**
1. User sends multipart/form-data with video file
2. Backend validates:
   - File extension (`.mp4`, `.mov`, `.avi`)
   - File size (max 500MB)
3. Creates `Video` record in PostgreSQL:
   ```sql
   INSERT INTO videos (id, user_id, title, status, file_size_bytes, original_filename)
   VALUES (uuid, user_id, title, 'UPLOADING', file_size, filename);
   ```
4. Saves original file:
   ```
   /app/uploads/originals/{video_id}.mp4
   ```
5. Updates video status to `PROCESSING`:
   ```sql
   UPDATE videos SET status = 'PROCESSING' WHERE id = video_id;
   ```

**Response to User:**
```json
{
  "video_id": "abc-123-def-456",
  "status": "processing",
  "message": "Video upload accepted, processing started"
}
```

---

### **Step 2: Backend Sends Task to Redis**

**Service:** FastAPI Backend → Redis  
**Method:** `celery_app.send_task()`

**Code Flow:**
```python
# backend/app/api/v1/videos.py
result = celery_app.send_task(
    "process_video",                    # Task name
    args=[str(video.id), str(file_path)],  # Arguments
    queue="celery",                     # Queue name
    ignore_result=True,                 # Don't wait for result
)
```

**What Happens:**
1. Backend's Celery app (`short_video_platform`) serializes task
2. Task message is sent to Redis broker
3. Message is placed in `celery` queue
4. Backend immediately returns (doesn't wait for processing)

**Redis Queue Structure:**
```
Redis Key: celery
Type: List (queue)
Value: [
  {
    "task": "process_video",
    "id": "task-uuid-here",
    "args": ["video-uuid", "/app/uploads/originals/video-uuid.mp4"],
    "kwargs": {},
    "retries": 0,
    "eta": null,
    "expires": null
  }
]
```

---

### **Step 3: Video Worker Receives Task**

**Service:** Video Worker (`short5_video_worker`)  
**Process:** Celery worker polling Redis queue

**Worker Configuration:**
```python
# video_worker/worker.py
celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

# Worker command (docker-compose.yml):
celery -A worker worker --loglevel=info --concurrency=2 -Q celery
```

**What Happens:**
1. Video worker continuously polls Redis `celery` queue
2. When task appears, worker:
   - Deserializes task message
   - Matches task name `"process_video"` to registered function
   - Executes `process_video(video_id, file_path)`

**Task Registration:**
```python
@celery_app.task(name="process_video", bind=True, max_retries=0)
def process_video(self, video_id: str, file_path: str):
    # Processing logic here
```

---

### **Step 4: Video Processing**

**Service:** Video Worker (`short5_video_worker`)  
**Task:** `process_video()`

**Processing Steps:**

#### 4.1 Validate Video File
```python
is_valid, error = validate_video_file(input_path)
# Uses ffprobe to check video format
```

#### 4.2 Transcode to MP4
```python
# FFmpeg command:
ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4
# Output: /tmp/video_processing/{video_id}/{video_id}.mp4
```

#### 4.3 Create Thumbnail
```python
# FFmpeg command:
ffmpeg -i input.mp4 -ss 00:00:01 -vframes 1 thumbnail.jpg
# Output: /tmp/video_processing/{video_id}/{video_id}_thumb.jpg
```

#### 4.4 Store Processed Files
```python
# Move files to final location:
/app/uploads/processed/{video_id}/video.mp4
/app/uploads/processed/{video_id}/thumbnail.jpg
```

#### 4.5 Update Database
```python
# Update video record:
update_video_status(video_id, "ready", 
    url_mp4="/uploads/processed/{video_id}/video.mp4",
    thumbnail="/uploads/processed/{video_id}/thumbnail.jpg",
    duration_seconds=45
)
```

**Database Update:**
```sql
UPDATE videos 
SET 
    status = 'ready',
    url_mp4 = '/uploads/processed/{video_id}/video.mp4',
    thumbnail = '/uploads/processed/{video_id}/thumbnail.jpg',
    duration_seconds = 45,
    error_reason = NULL
WHERE id = '{video_id}';
```

---

## 🔄 Service Communication Patterns

### **Pattern 1: Backend → Redis → Video Worker**

```
┌──────────┐         ┌──────────┐         ┌──────────────┐
│ Backend  │────────▶│  Redis   │────────▶│Video Worker  │
│          │ send    │          │ poll    │              │
│          │ task    │  Queue   │ task    │              │
└──────────┘         └──────────┘         └──────────────┘
     │                     │                      │
     │                     │                      │
     │                     │                      ▼
     │                     │              ┌──────────────┐
     │                     │              │  PostgreSQL  │
     │                     │              │   (Update)    │
     │                     │              └──────────────┘
     │                     │
     ▼                     ▼
┌──────────┐         ┌──────────┐
│Database  │         │  Flower  │
│(Read)    │         │(Monitor) │
└──────────┘         └──────────┘
```

### **Pattern 2: Task Message Flow**

```
Backend creates task
    │
    ├─▶ Serialize task (JSON)
    │
    ├─▶ Send to Redis broker
    │   └─▶ redis://redis:6379/0
    │
    ├─▶ Add to queue: "celery"
    │
    └─▶ Return task_id to backend
        │
        └─▶ Backend logs: "Task queued: {task_id}"

Video Worker polls queue
    │
    ├─▶ Check Redis queue "celery"
    │
    ├─▶ Dequeue task message
    │
    ├─▶ Deserialize task (JSON)
    │
    ├─▶ Match task name: "process_video"
    │
    └─▶ Execute: process_video(video_id, file_path)
```

---

## 🗄️ Data Flow Through Services

### **1. File Storage Flow**

```
User Upload
    │
    ▼
┌─────────────────────────────────────┐
│ /app/uploads/originals/             │
│   └─ {video_id}.mp4                 │
│      (Original uploaded file)       │
└─────────────────────────────────────┘
    │
    │ (Video Worker reads)
    │
    ▼
┌─────────────────────────────────────┐
│ /tmp/video_processing/{video_id}/   │
│   ├─ {video_id}.mp4                 │
│   └─ {video_id}_thumb.jpg           │
│      (Temporary processing)          │
└─────────────────────────────────────┘
    │
    │ (Video Worker moves)
    │
    ▼
┌─────────────────────────────────────┐
│ /app/uploads/processed/{video_id}/  │
│   ├─ video.mp4                      │
│   └─ thumbnail.jpg                  │
│      (Final processed files)        │
└─────────────────────────────────────┘
```

### **2. Database Status Flow**

```
┌─────────────┐
│ UPLOADING   │  ← Created when file upload starts
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PROCESSING  │  ← Set when task sent to Redis
└──────┬──────┘
       │
       ├─▶ (Processing happens in background)
       │
       ▼
┌─────────────┐
│   READY     │  ← Set when processing completes
└─────────────┘
       │
       └─▶ OR
           ▼
    ┌─────────────┐
    │   ERROR     │  ← Set if processing fails
    └─────────────┘
```

### **3. Redis Queue States**

```
Empty Queue (No tasks)
┌──────────┐
│  Redis   │
│  Queue:  │
│  "celery"│  []
└──────────┘

Task Queued
┌──────────┐
│  Redis   │
│  Queue:  │
│  "celery"│  [Task1, Task2, Task3]
└──────────┘
    │
    │ Worker polls
    │
    ▼
┌──────────┐
│  Redis   │
│  Queue:  │
│  "celery"│  [Task2, Task3]  ← Task1 dequeued
└──────────┘
```

---

## 🔍 Monitoring with Celery Flower

### **What Flower Shows:**

1. **Workers Tab:**
   - `celery@short5_celery_worker` - General worker
   - `celery@short5_video_worker` - Video processing worker
   - Active tasks, processed tasks, worker status

2. **Tasks Tab:**
   - All `process_video` tasks
   - Task state: PENDING → STARTED → SUCCESS/FAILURE
   - Task duration, arguments, results

3. **Monitor Tab:**
   - Real-time task execution
   - Task rate, worker activity
   - Queue depth

4. **Broker Tab:**
   - Redis connection status
   - Queue statistics
   - Message rates

### **Example Flower View:**

```
Dashboard
├─ Workers: 2 active
│  ├─ celery@short5_video_worker (2 active tasks)
│  └─ celery@short5_celery_worker (idle)
│
├─ Tasks: 150 total
│  ├─ process_video: 145
│  │  ├─ SUCCESS: 140
│  │  ├─ FAILURE: 3
│  │  └─ PENDING: 2
│
└─ Queue: celery
   └─ Length: 2 (tasks waiting)
```

---

## 🛠️ Troubleshooting Guide

### **Issue: Task Not Reaching Worker**

**Check:**
1. Redis connection:
   ```bash
   docker-compose exec redis redis-cli PING
   # Should return: PONG
   ```

2. Queue contents:
   ```bash
   docker-compose exec redis redis-cli LLEN celery
   # Shows number of tasks in queue
   ```

3. Worker logs:
   ```bash
   docker-compose logs -f video_worker
   # Should show: "celery@... ready"
   ```

### **Issue: Task Stuck in PROCESSING**

**Check:**
1. Flower dashboard: http://localhost:5555
   - Look for task in "Tasks" tab
   - Check task state (STARTED, FAILURE, etc.)

2. Worker logs:
   ```bash
   docker-compose logs video_worker | grep {video_id}
   ```

3. Database status:
   ```sql
   SELECT id, status, error_reason FROM videos WHERE id = '{video_id}';
   ```

### **Issue: File Not Found**

**Check:**
1. File exists:
   ```bash
   docker-compose exec backend ls -la /app/uploads/originals/{video_id}*
   ```

2. Volume mounts:
   ```bash
   docker-compose exec video_worker ls -la /app/uploads/originals/
   ```

---

## 📊 Service Dependencies

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐      ┌─────────────┐
│   Backend   │──────▶│ PostgreSQL  │
│  (FastAPI)  │      │  (Database) │
└──────┬──────┘      └─────────────┘
       │
       │ Celery Task
       ▼
┌─────────────┐
│    Redis    │◀──────┐
│   (Broker)  │       │
└──────┬──────┘       │
       │              │
       │              │
       ▼              │
┌─────────────┐       │
│Video Worker │───────┘
│  (Celery)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │
│  (Update)   │
└─────────────┘
```

---

## 🔑 Key Concepts

### **1. Celery App Separation**

- **Backend App:** `short_video_platform` (sends tasks)
- **Worker App:** `worker` (executes tasks)
- **Communication:** Both use same Redis broker

### **2. Task Routing**

```python
# Backend routes task to "celery" queue
task_routes = {
    "process_video": {"queue": "celery"}
}

# Worker listens to "celery" queue
celery -A worker worker -Q celery
```

### **3. Async Processing**

- Backend returns immediately (202 Accepted)
- Processing happens in background
- Status checked via database or Flower

### **4. Shared Storage**

- Both backend and video_worker mount:
  - `/app/uploads` (Docker volume)
- Backend writes: `/app/uploads/originals/`
- Worker reads/writes: `/app/uploads/processed/`

---

## 📝 Summary

**The video upload process involves:**

1. **User** → Uploads video to **Backend**
2. **Backend** → Saves file, creates DB record, sends task to **Redis**
3. **Redis** → Queues task message
4. **Video Worker** → Polls Redis, receives task, processes video
5. **Video Worker** → Updates **PostgreSQL** with results
6. **Flower** → Monitors entire process in real-time

**Key Technologies:**
- **Celery:** Distributed task queue
- **Redis:** Message broker and queue storage
- **PostgreSQL:** Persistent data storage
- **Docker Volumes:** Shared file storage
- **FFmpeg:** Video processing

This architecture allows:
- ✅ Non-blocking uploads (user doesn't wait)
- ✅ Scalable processing (multiple workers)
- ✅ Fault tolerance (tasks can be retried)
- ✅ Observability (Flower monitoring)
