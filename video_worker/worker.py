"""
FFmpeg Video Processing Worker
Processes videos: transcodes to HLS, creates thumbnails, uploads to S3/R2
"""
import os
import subprocess
import asyncio
from pathlib import Path
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Celery app
celery_app = Celery(
    "video_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
# Use psycopg2 for synchronous database access in Celery worker
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# S3/R2 client
s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)
S3_BUCKET = os.getenv("S3_BUCKET_NAME")

# Processing settings
TEMP_DIR = Path("/tmp/video_processing")
TEMP_DIR.mkdir(exist_ok=True)

# Video encoding settings
VIDEO_PROFILES = {
    "720p": {
        "resolution": "1280x720",
        "bitrate": "2500k",
        "audio_bitrate": "128k",
    },
    "480p": {
        "resolution": "854x480",
        "bitrate": "1000k",
        "audio_bitrate": "96k",
    },
}


def update_video_status(video_id: str, status: str, **kwargs):
    """Update video status in database"""
    with SessionLocal() as session:
        update_fields = {"status": status}
        update_fields.update(kwargs)
        
        set_clause = ", ".join([f"{k} = :{k}" for k in update_fields.keys()])
        query = text(f"""
            UPDATE videos 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :video_id
        """)
        
        params = {"video_id": video_id, **update_fields}
        session.execute(query, params)
        session.commit()


def transcode_to_hls(input_path: Path, output_dir: Path, video_id: str):
    """
    Transcode video to HLS format with multiple quality levels
    """
    hls_playlist = output_dir / f"{video_id}.m3u8"
    
    # Create HLS segments for each quality
    for quality, profile in VIDEO_PROFILES.items():
        segment_dir = output_dir / quality
        segment_dir.mkdir(exist_ok=True)
        
        segment_pattern = str(segment_dir / f"{video_id}_%03d.ts")
        playlist_file = segment_dir / f"{video_id}.m3u8"
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:v", profile["bitrate"],
            "-b:a", profile["audio_bitrate"],
            "-s", profile["resolution"],
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-hls_segment_filename", segment_pattern,
            "-f", "hls",
            str(playlist_file),
        ]
        
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
    
    # Create master playlist
    master_playlist_content = "#EXTM3U\n"
    for quality in VIDEO_PROFILES.keys():
        master_playlist_content += f'#EXT-X-STREAM-INF:BANDWIDTH={VIDEO_PROFILES[quality]["bitrate"]}\n'
        master_playlist_content += f"{quality}/{video_id}.m3u8\n"
    
    hls_playlist.write_text(master_playlist_content)
    return hls_playlist


def create_thumbnail(input_path: Path, output_path: Path, timestamp: str = "00:00:01"):
    """Create thumbnail from video"""
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-ss", timestamp,
        "-vframes", "1",
        "-q:v", "2",
        str(output_path),
    ]
    subprocess.run(ffmpeg_cmd, check=True, capture_output=True)


def upload_to_s3(local_path: Path, s3_key: str):
    """Upload file to S3/R2"""
    try:
        s3_client.upload_file(
            str(local_path),
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "application/octet-stream"},
        )
        return f"https://{S3_BUCKET}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_key}"
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        raise


@celery_app.task(name="process_video")
def process_video(video_id: str, file_path: str):
    """
    Main video processing task
    """
    try:
        update_video_status(video_id, "processing")
        
        input_path = Path(file_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")
        
        # Create output directory
        output_dir = TEMP_DIR / video_id
        output_dir.mkdir(exist_ok=True)
        
        # Transcode to HLS
        hls_playlist = transcode_to_hls(input_path, output_dir, video_id)
        
        # Create thumbnail
        thumbnail_path = output_dir / f"{video_id}_thumb.jpg"
        create_thumbnail(input_path, thumbnail_path)
        
        # Upload to S3/R2
        hls_url = upload_to_s3(hls_playlist, f"videos/{video_id}/playlist.m3u8")
        
        # Upload HLS segments
        for quality in VIDEO_PROFILES.keys():
            segment_dir = output_dir / quality
            for segment_file in segment_dir.glob("*.ts"):
                s3_key = f"videos/{video_id}/{quality}/{segment_file.name}"
                upload_to_s3(segment_file, s3_key)
            
            # Upload quality playlist
            quality_playlist = segment_dir / f"{video_id}.m3u8"
            s3_key = f"videos/{video_id}/{quality}/{quality_playlist.name}"
            upload_to_s3(quality_playlist, s3_key)
        
        # Upload thumbnail
        thumbnail_url = upload_to_s3(thumbnail_path, f"videos/{video_id}/thumbnail.jpg")
        
        # Get video duration
        ffprobe_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ]
        duration = float(subprocess.run(ffprobe_cmd, capture_output=True, text=True).stdout.strip())
        
        # Update database
        update_video_status(
            video_id,
            "ready",
            url_hls=hls_url,
            thumbnail=thumbnail_url,
            duration_seconds=int(duration),
        )
        
        # Cleanup temp files
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
        
        return {"status": "success", "video_id": video_id}
        
    except Exception as e:
        update_video_status(video_id, "failed")
        print(f"Error processing video {video_id}: {e}")
        raise


if __name__ == "__main__":
    celery_app.start()

