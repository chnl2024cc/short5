"""
Video Processing Tasks (Celery)
"""
from app.celery_app import celery_app


@celery_app.task(name="process_video")
def process_video(video_id: str):
    """
    Process video: transcode to HLS, create thumbnail
    This task is triggered by the video worker
    """
    # Implementation will be in video_worker
    pass

