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


def cleanup_failed_video(video_id: str, file_path: Path):
    """
    Clean up files for a failed video
    
    Removes:
    - Original uploaded file
    - Processed files (HLS segments, playlists, thumbnails)
    - Temporary processing directories
    """
    import shutil
    
    cleaned = []
    
    # Clean up original file
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            cleaned.append(f"original file: {file_path}")
    except Exception as e:
        print(f"  ⚠ Could not clean up original file {file_path}: {e}")
    
    # Clean up processed files (look for files with video_id in name)
    try:
        processed_dir = Path(f"/app/uploads/processed")
        if processed_dir.exists():
            for processed_file in processed_dir.glob(f"*{video_id}*"):
                try:
                    if processed_file.is_file():
                        processed_file.unlink()
                        cleaned.append(f"processed file: {processed_file.name}")
                    elif processed_file.is_dir():
                        shutil.rmtree(processed_file, ignore_errors=True)
                        cleaned.append(f"processed directory: {processed_file.name}")
                except Exception as e:
                    print(f"  ⚠ Could not clean up {processed_file}: {e}")
    except Exception as e:
        print(f"  ⚠ Could not clean up processed files: {e}")
    
    # Clean up temp directory
    try:
        temp_dir = Path(f"/tmp/video_processing/{video_id}")
        if temp_dir.exists() and temp_dir.is_dir():
            shutil.rmtree(temp_dir, ignore_errors=True)
            cleaned.append(f"temp directory: {temp_dir}")
    except Exception as e:
        print(f"  ⚠ Could not clean up temp directory {temp_dir}: {e}")
    
    if cleaned:
        print(f"  🗑️ Cleaned up {len(cleaned)} item(s) for failed video")
    else:
        print(f"  ℹ️ No files to clean up for failed video")
    return cleaned


def validate_video_file(file_path: Path) -> tuple[bool, Optional[str]]:
    """
    Validate video file before processing
    Returns: (is_valid, error_message)
    """
    # Check file exists
    if not file_path.exists():
        return False, "Video file not found"
    
    # Check file is not empty
    if file_path.stat().st_size == 0:
        return False, "Video file is empty or corrupted"
    
    # Check file is readable
    if not os.access(file_path, os.R_OK):
        return False, "Video file is not readable"
    
    # Try to get basic video info with ffprobe to check if file is valid
    try:
        ffprobe_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        result = subprocess.run(
            ffprobe_cmd,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )
        
        if result.returncode != 0:
            return False, f"Video file is corrupted or invalid format: {result.stderr[:200]}"
        
        # Check if duration is valid
        try:
            duration = float(result.stdout.strip())
            if duration <= 0:
                return False, "Video has invalid duration (0 or negative)"
        except (ValueError, AttributeError):
            return False, "Could not determine video duration - file may be corrupted"
        
    except subprocess.TimeoutExpired:
        return False, "Video file validation timed out - file may be corrupted"
    except Exception as e:
        return False, f"Error validating video file: {str(e)[:200]}"
    
    return True, None


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


@celery_app.task(name="process_video", bind=True, max_retries=0)
def process_video(self, video_id: str, file_path: str):
    """
    Main video processing task with comprehensive error handling
    
    Args:
        video_id: UUID of the video record
        file_path: Path to the uploaded video file
    """
    input_path = Path(file_path)
    error_category = None
    user_friendly_error = None
    
    try:
        print(f"📹 Starting video processing for {video_id}")
        print(f"   File path: {file_path}")
        
        # Update status to processing (in case it wasn't already)
        update_video_status(video_id, "processing", error_reason=None)
        
        # Step 1: Validate video file
        print("  → Validating video file...")
        is_valid, validation_error = validate_video_file(input_path)
        if not is_valid:
            error_category = "VALIDATION_ERROR"
            user_friendly_error = f"Video file validation failed: {validation_error}"
            print(f"✗ {user_friendly_error}")
            raise ValueError(validation_error)
        print("  ✓ Video file is valid")
        
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
        
        # Step 4: Upload to S3/R2 (per RFC: Video dann auf CDN ausliefern)
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
            error_category = "STORAGE_ERROR"
            user_friendly_error = "Failed to store processed video files."
            print(f"✗ ERROR during upload: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Step 5: Get video duration
        try:
            ffprobe_cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(input_path),
            ]
            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise ValueError(f"Could not get video duration: {result.stderr}")
            duration = float(result.stdout.strip())
        except Exception as e:
            error_category = "METADATA_ERROR"
            user_friendly_error = "Could not extract video metadata."
            print(f"✗ ERROR getting video duration: {e}")
            raise
        
        # Step 6: Update database with processed video URLs
        update_data = {
            "status": "ready",
            "url_hls": hls_url,
            "duration_seconds": int(duration),
            "error_reason": None,  # Clear any previous errors
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
        
        # Determine error category and user-friendly message if not already set
        if not error_category:
            if isinstance(e, FileNotFoundError):
                error_category = "FILE_NOT_FOUND"
                user_friendly_error = "Video file was not found. Please try uploading again."
            elif isinstance(e, ValueError):
                error_category = "PROCESSING_ERROR"
                if not user_friendly_error:
                    user_friendly_error = "Video processing failed. The file may be corrupted or in an unsupported format."
            elif isinstance(e, subprocess.CalledProcessError):
                error_category = "TRANSCODING_ERROR"
                user_friendly_error = "Video transcoding failed. The file may be corrupted or in an unsupported format."
            else:
                error_category = "UNKNOWN_ERROR"
                user_friendly_error = "An unexpected error occurred during video processing. Please try uploading again."
        
        print(f"✗ ERROR processing video {video_id}: {e}")
        print(f"Error category: {error_category}")
        print(f"Error details:\n{error_details}")
        
        # Update database with failure status and error reason
        error_message = user_friendly_error or str(e)[:500]  # Limit error message length
        update_video_status(video_id, "failed", error_reason=error_message)
        
        # Cleanup files for failed video
        print(f"  → Cleaning up files for failed video...")
        cleanup_failed_video(video_id, input_path)
        
        # Don't re-raise - we've handled the error and cleaned up
        return {"status": "failed", "video_id": video_id, "error": error_message}


# Make celery_app available for Celery CLI
# When running: celery -A worker worker
# Celery will import this module and use celery_app

