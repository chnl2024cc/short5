"""
Video Processing Tasks (Celery)
Note: The actual video processing is done by the video_worker service.
This file is kept for potential future backend tasks, but video processing
is handled entirely by the video_worker service via the "process_video" task.
"""
# No task definition needed here - video_worker/worker.py defines the actual task
# Backend just sends tasks using celery_app.send_task("process_video", ...)

