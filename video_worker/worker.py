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
    "worker",  # Use "worker" as the main module name
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    # Accept tasks from any Celery app (since backend uses different app name)
    task_accept_content=["json"],
    worker_prefetch_multiplier=1,  # Process one task at a time for video processing
)

# Explicitly register the task (no autodiscover needed for single file)
# The @celery_app.task decorator below will register it automatically

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Use psycopg2 for synchronous database access in Celery worker
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
elif DATABASE_URL.startswith("postgresql+psycopg2://"):
    pass  # Already correct
else:
    raise ValueError(f"Invalid DATABASE_URL format: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# S3/R2 client (only initialize if credentials are provided)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")

# Only create S3 client if credentials are available
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    s3_client = boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
else:
    s3_client = None
    print("S3 credentials not provided - will use local file storage (development mode)")

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
        
        result = subprocess.run(
            ffmpeg_cmd, 
            check=True, 
            capture_output=True,
            text=True
        )
        # Log FFmpeg output if there are warnings (stderr)
        if result.stderr:
            # FFmpeg outputs info to stderr, but errors are also there
            # Only log if it looks like an error (contains "Error" or "error")
            if "error" in result.stderr.lower():
                print(f"    FFmpeg warning/error for {quality}: {result.stderr[:200]}")
    
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
    """Upload file to S3/R2, or use local file path in development mode"""
    # Development mode: if S3 credentials are not configured, use local file paths
    if not S3_BUCKET or s3_client is None:
        print(f"📦 Development mode: Using local file storage for {s3_key}")
        try:
            # Return a local file URL that can be served by the backend
            # Store files in a local directory that the backend can serve
            local_storage = Path("/app/uploads/processed")
            local_storage.mkdir(parents=True, exist_ok=True)
            
            # Copy file to processed directory
            # Use a cleaner path structure: preserve directory structure but make it URL-safe
            safe_key = s3_key.replace("/", "_")
            dest_path = local_storage / safe_key
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(local_path, dest_path)
            
            # Verify file was copied
            if not dest_path.exists():
                raise FileNotFoundError(f"Failed to copy file to {dest_path}")
            
            # Return a path that backend can serve (backend mounts /uploads)
            url_path = f"/uploads/processed/{safe_key}"
            print(f"  ✓ File stored locally: {dest_path} → {url_path}")
            return url_path
        except Exception as e:
            print(f"✗ ERROR in local file storage: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: return path to original file location if copy fails
            # This is a last resort - should not normally happen
            print(f"  ⚠ Falling back to original file location")
            return f"/uploads/{local_path.name}"
    
    # Production mode: upload to S3/R2
    try:
        print(f"📦 Production mode: Uploading {s3_key} to S3/R2")
        s3_client.upload_file(
            str(local_path),
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "application/octet-stream"},
        )
        # Use endpoint URL if provided (for Cloudflare R2)
        if os.getenv("S3_ENDPOINT_URL"):
            url = f"{os.getenv('S3_ENDPOINT_URL')}/{S3_BUCKET}/{s3_key}"
        else:
            url = f"https://{S3_BUCKET}.s3.{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com/{s3_key}"
        print(f"  ✓ Uploaded to S3: {url}")
        return url
    except ClientError as e:
        print(f"✗ ERROR uploading to S3: {e}")
        import traceback
        traceback.print_exc()
        raise
    except Exception as e:
        print(f"✗ ERROR in S3 upload (unexpected): {e}")
        import traceback
        traceback.print_exc()
        raise


@celery_app.task(name="process_video")
def process_video(video_id: str, file_path: str):
    """
    Main video processing task
    """
    try:
        print(f"📹 Starting video processing for {video_id}")
        print(f"   File path: {file_path}")
        
        # Update status to processing (in case it wasn't already)
        update_video_status(video_id, "processing")
        
        input_path = Path(file_path)
        if not input_path.exists():
            error_msg = f"Video file not found: {file_path}"
            print(f"✗ ERROR: {error_msg}")
            raise FileNotFoundError(error_msg)
        
        print(f"✓ File found, starting transcoding...")
        
        # Create output directory
        output_dir = TEMP_DIR / video_id
        output_dir.mkdir(exist_ok=True)
        
        # Transcode to HLS (per RFC: HLS + mp4)
        print("  → Transcoding to HLS format...")
        hls_playlist = transcode_to_hls(input_path, output_dir, video_id)
        print("  ✓ HLS transcoding complete")
        
        # Create thumbnail (per RFC: Thumbnail + Preview)
        print("  → Creating thumbnail...")
        thumbnail_path = output_dir / f"{video_id}_thumb.jpg"
        create_thumbnail(input_path, thumbnail_path)
        print("  ✓ Thumbnail created")
        
        # Upload to S3/R2 (per RFC: Video dann auf CDN ausliefern)
        print("  → Uploading to storage...")
        try:
            hls_url = upload_to_s3(hls_playlist, f"videos/{video_id}/playlist.m3u8")
            
            # Upload HLS segments
            segment_count = 0
            for quality in VIDEO_PROFILES.keys():
                segment_dir = output_dir / quality
                for segment_file in segment_dir.glob("*.ts"):
                    s3_key = f"videos/{video_id}/{quality}/{segment_file.name}"
                    upload_to_s3(segment_file, s3_key)
                    segment_count += 1
                
                # Upload quality playlist
                quality_playlist = segment_dir / f"{video_id}.m3u8"
                if quality_playlist.exists():
                    s3_key = f"videos/{video_id}/{quality}/{quality_playlist.name}"
                    upload_to_s3(quality_playlist, s3_key)
            
            # Upload thumbnail (if it was created successfully)
            thumbnail_url = None
            if thumbnail_path and thumbnail_path.exists():
                thumbnail_url = upload_to_s3(thumbnail_path, f"videos/{video_id}/thumbnail.jpg")
            print(f"  ✓ Upload complete ({segment_count} segments + playlists" + (f" + thumbnail" if thumbnail_url else "") + ")")
        except Exception as e:
            print(f"✗ ERROR during upload: {e}")
            import traceback
            traceback.print_exc()
            # Set default URLs so video can still be marked as ready (with original file)
            # Try to use the original uploaded file as fallback
            hls_url = f"/uploads/{Path(file_path).name}"  # Fallback to original file
            thumbnail_url = None
            print(f"  ⚠ Using fallback URLs (original file)")
        
        # Get video duration
        ffprobe_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ]
        duration = float(subprocess.run(ffprobe_cmd, capture_output=True, text=True).stdout.strip())
        
        # Update database with processed video URLs
        update_data = {
            "status": "ready",
            "url_hls": hls_url,
            "duration_seconds": int(duration),
        }
        if thumbnail_url:
            update_data["thumbnail"] = thumbnail_url
        
        update_video_status(video_id, **update_data)
        
        print(f"✓ Video {video_id} processed successfully")
        print(f"  HLS URL: {hls_url}")
        print(f"  Thumbnail: {thumbnail_url}")
        
        # Cleanup temp files
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
        
        return {"status": "success", "video_id": video_id}
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"✗ ERROR processing video {video_id}: {e}")
        print(f"Error details:\n{error_details}")
        update_video_status(video_id, "failed")
        raise


# Make celery_app available for Celery CLI
# When running: celery -A worker worker
# Celery will import this module and use celery_app

