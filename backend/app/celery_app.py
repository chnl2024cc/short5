"""
Celery Application Configuration
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "short_video_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # No need to include video_processing - video_worker handles it
    # Backend just sends tasks, doesn't need to define them
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Route process_video tasks to default celery queue (video_worker listens to this)
    task_routes={
        "process_video": {"queue": "celery"},
        # Also handle fully qualified task names from other apps
        "worker.process_video": {"queue": "celery"},
    },
    # Allow sending tasks that aren't defined in this app (video_worker defines them)
    task_ignore_result=True,  # We don't need results for video processing
    # Ensure tasks can be sent to other apps
    task_always_eager=False,
)

