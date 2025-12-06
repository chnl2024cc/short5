"""
FFmpeg Video Processing Worker
Processes videos: transcodes to MP4, creates thumbnails, stores in local Docker volume
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Optional
# boto3 removed - using local storage only
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
    # Allow receiving tasks from other Celery apps (backend uses "short_video_platform")
    task_ignore_result=True,
    # Ensure we can receive tasks sent via send_task from other apps
    imports=("worker",),  # Explicitly import this module to register tasks
    # Accept tasks with or without app prefix
    task_routes={
        "process_video": {"queue": "celery"},
        "worker.process_video": {"queue": "celery"},
        "short_video_platform.process_video": {"queue": "celery"},  # Accept from backend app
    },
    # Don't reject tasks on worker lost
    task_reject_on_worker_lost=False,
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

# Local storage only - no S3/R2
# All files stored in /app/uploads/processed/ directory structure
print("📦 Using local file storage (Docker volume)")

# Processing settings
TEMP_DIR = Path("/tmp/video_processing")
TEMP_DIR.mkdir(exist_ok=True)

def update_video_status(video_id: str, status: str, **kwargs):
    """Update video status in database"""
    from uuid import UUID
    
    try:
        with SessionLocal() as session:
            update_fields = {"status": status}
            update_fields.update(kwargs)
            
            print(f"  → Updating video {video_id}: status={status}")
            
            # Convert video_id to UUID
            video_uuid = UUID(video_id) if isinstance(video_id, str) else video_id
            
            # Build SQL with explicit parameter binding for each field
            # This avoids issues with dynamic SQL generation
            set_clauses = []
            params = {"video_id": str(video_uuid)}
            
            for key, value in update_fields.items():
                param_name = f"val_{key}"
                set_clauses.append(f"{key} = :{param_name}")
                params[param_name] = value
            
            # Build the UPDATE query
            set_clause = ", ".join(set_clauses)
            query = text(f"""
                UPDATE videos 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = CAST(:video_id AS uuid)
            """)
            
            result = session.execute(query, params)
            session.commit()
            
            if result.rowcount == 0:
                print(f"  ⚠ No rows updated for video {video_id}")
            else:
                print(f"  ✓ Database updated")
                
    except Exception as e:
        print(f"✗ ERROR updating video status: {e}")
        raise


def cleanup_failed_video(video_id: str, file_path: Path):
    """
    Clean up files for a failed video
    
    Removes:
    - Original uploaded file
    - Processed files (MP4 outputs, thumbnails)
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


def check_mp4_faststart(file_path: Path) -> bool:
    """
    Check if MP4 file has faststart (moov atom before mdat atom)
    Faststart means the metadata is at the beginning, allowing streaming without full download
    
    Returns:
        True if faststart is enabled (moov before mdat), False otherwise
    """
    try:
        # Read first 64KB to check atom order (moov should appear early if faststart is enabled)
        with open(file_path, 'rb') as f:
            header = f.read(65536)  # 64KB should be enough to find moov atom if it's at the start
        
        # Find positions of key atoms
        moov_pos = header.find(b'moov')
        mdat_pos = header.find(b'mdat')
        
        # If moov is not found, file might be corrupted or not a valid MP4
        if moov_pos == -1:
            return False
        
        # Faststart means moov comes before mdat
        # If mdat is not found in header, moov is definitely at the start (good sign)
        if mdat_pos == -1:
            return True
        
        # Check if moov comes before mdat
        return moov_pos < mdat_pos
        
    except Exception as e:
        print(f"  ⚠ Could not check faststart: {e}")
        return False


def get_video_metadata(file_path: Path) -> tuple[Optional[dict], Optional[str]]:
    """
    Get all video metadata in a single ffprobe call
    
    Returns:
        (metadata_dict, error_message)
        metadata_dict contains: format_name, duration, is_mp4, has_faststart
    """
    try:
        # Single ffprobe call to get format name and duration
        ffprobe_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=format_name:format=duration",
            "-of", "json",  # Use JSON for structured output
            str(file_path),
        ]
        
        result = subprocess.run(
            ffprobe_cmd,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )
        
        if result.returncode != 0:
            return None, f"Could not probe video file: {result.stderr[:200]}"
        
        # Parse JSON output
        try:
            probe_data = json.loads(result.stdout)
            format_info = probe_data.get("format", {})
            
            format_name = format_info.get("format_name", "").lower()
            duration_str = format_info.get("duration")
            
            if not duration_str:
                return None, "Could not determine video duration"
            
            try:
                duration = float(duration_str)
                if duration <= 0:
                    return None, "Video has invalid duration (0 or negative)"
            except (ValueError, TypeError):
                return None, "Could not parse video duration"
            
            # Check if it's MP4 format
            is_mp4 = "mp4" in format_name or "mov" in format_name
            
            # Check faststart for MP4 files
            has_faststart = False
            if is_mp4 and file_path.suffix.lower() == ".mp4":
                has_faststart = check_mp4_faststart(file_path)
            
            metadata = {
                "format_name": format_name,
                "duration": duration,
                "is_mp4": is_mp4,
                "has_faststart": has_faststart,
            }
            
            return metadata, None
            
        except json.JSONDecodeError as e:
            return None, f"Could not parse ffprobe output: {str(e)[:200]}"
        
    except subprocess.TimeoutExpired:
        return None, "Video metadata extraction timed out"
    except Exception as e:
        return None, f"Error getting video metadata: {str(e)[:200]}"


def get_detailed_video_metadata(file_path: Path) -> tuple[Optional[dict], Optional[str]]:
    """
    Get detailed technical metadata from processed video file
    Includes codecs, bitrates, resolution, FPS, faststart status, etc.
    
    Returns:
        (metadata_dict, error_message)
        metadata_dict contains all technical video information for database storage
    """
    try:
        # Comprehensive ffprobe call to get all technical metadata
        ffprobe_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries",
            "format=format_name:format=bit_rate:format=duration:format=size",
            "-show_entries",
            "stream=codec_name:stream=codec_type:stream=bit_rate:stream=width:stream=height:stream=r_frame_rate:stream=pix_fmt:stream=sample_rate:stream=channels",
            "-of", "json",
            str(file_path),
        ]
        
        result = subprocess.run(
            ffprobe_cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            return None, f"Could not probe video file: {result.stderr[:200]}"
        
        try:
            probe_data = json.loads(result.stdout)
            format_info = probe_data.get("format", {})
            streams = probe_data.get("streams", [])
            
            # Extract video stream info (usually first video stream)
            video_stream = None
            audio_stream = None
            
            for stream in streams:
                codec_type = stream.get("codec_type", "").lower()
                if codec_type == "video" and video_stream is None:
                    video_stream = stream
                elif codec_type == "audio" and audio_stream is None:
                    audio_stream = stream
            
            # Build metadata dictionary
            metadata = {}
            
            # Format info
            format_name = format_info.get("format_name", "").lower()
            metadata["container_format"] = format_name
            
            # File size
            if "size" in format_info:
                try:
                    metadata["file_size_bytes"] = int(format_info["size"])
                except (ValueError, TypeError):
                    pass
            
            # Total bitrate (format level)
            if "bit_rate" in format_info:
                try:
                    metadata["total_bitrate_bps"] = int(format_info["bit_rate"])
                except (ValueError, TypeError):
                    pass
            
            # Video stream info
            if video_stream:
                metadata["video_codec"] = video_stream.get("codec_name", "").lower()
                
                if "width" in video_stream and "height" in video_stream:
                    width = video_stream.get("width")
                    height = video_stream.get("height")
                    if width and height:
                        metadata["resolution_width"] = int(width)
                        metadata["resolution_height"] = int(height)
                        metadata["resolution"] = f"{width}x{height}"
                
                if "bit_rate" in video_stream:
                    try:
                        metadata["video_bitrate_bps"] = int(video_stream["bit_rate"])
                    except (ValueError, TypeError):
                        pass
                
                if "r_frame_rate" in video_stream:
                    # Parse frame rate (e.g., "30/1" -> 30.0)
                    fps_str = video_stream["r_frame_rate"]
                    try:
                        if "/" in fps_str:
                            num, den = fps_str.split("/")
                            metadata["fps"] = round(float(num) / float(den), 2)
                        else:
                            metadata["fps"] = float(fps_str)
                    except (ValueError, ZeroDivisionError):
                        pass
                
                if "pix_fmt" in video_stream:
                    metadata["pixel_format"] = video_stream["pix_fmt"]
            
            # Audio stream info
            if audio_stream:
                metadata["audio_codec"] = audio_stream.get("codec_name", "").lower()
                
                if "bit_rate" in audio_stream:
                    try:
                        metadata["audio_bitrate_bps"] = int(audio_stream["bit_rate"])
                    except (ValueError, TypeError):
                        pass
                
                if "sample_rate" in audio_stream:
                    try:
                        metadata["audio_sample_rate_hz"] = int(audio_stream["sample_rate"])
                    except (ValueError, TypeError):
                        pass
                
                if "channels" in audio_stream:
                    try:
                        metadata["audio_channels"] = int(audio_stream["channels"])
                    except (ValueError, TypeError):
                        pass
            
            # Check faststart for MP4 files
            if format_name and "mp4" in format_name and file_path.suffix.lower() == ".mp4":
                metadata["has_faststart"] = check_mp4_faststart(file_path)
            else:
                metadata["has_faststart"] = False
            
            # Web playback compatibility flags
            metadata["web_optimized"] = (
                metadata.get("video_codec") in ["h264", "avc"] and
                metadata.get("audio_codec") in ["aac", "mp3"] and
                metadata.get("has_faststart", False) and
                format_name and "mp4" in format_name
            )
            
            return metadata, None
            
        except json.JSONDecodeError as e:
            return None, f"Could not parse ffprobe output: {str(e)[:200]}"
        
    except subprocess.TimeoutExpired:
        return None, "Detailed video metadata extraction timed out"
    except Exception as e:
        return None, f"Error getting detailed video metadata: {str(e)[:200]}"


def transcode_to_mp4(input_path: Path, output_path: Path):
    """
    Transcode video to MP4 format optimized for web playback
    Uses H.264 video codec and AAC audio codec for maximum browser compatibility
    """
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",  # Good quality/size balance
        "-c:a", "aac",
        "-b:a", "128k",  # Audio bitrate
        "-movflags", "+faststart",  # Optimize for web streaming (metadata at beginning)
        "-pix_fmt", "yuv420p",  # Ensure compatibility
        "-y",  # Overwrite output file
        str(output_path),
    ]
    
    # Timeout: 25 minutes (slightly less than Celery's soft_time_limit of 25 min)
    # This ensures we have time for cleanup before hard timeout
    timeout_seconds = 25 * 60
    
    result = subprocess.run(
        ffmpeg_cmd,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds
    )
    
    if result.stderr and "error" in result.stderr.lower():
        print(f"    FFmpeg warning/error: {result.stderr[:200]}")
    
    return output_path


def create_thumbnail(input_path: Path, output_path: Path, timestamp: str = "00:00:03"):
    """
    Create thumbnail from video
    
    Args:
        input_path: Path to input video file
        output_path: Path where thumbnail will be saved
        timestamp: Timestamp to capture frame from (default: "00:00:03" = 3 seconds)
                   Use "00:00:00" for the first frame, or any other timestamp
    """
    # Put -ss before -i for faster seeking (seeks before decoding)
    # This is much faster for formats that support it
    ffmpeg_cmd = [
        "ffmpeg",
        "-ss", timestamp,  # Seek before input (faster)
        "-i", str(input_path),
        "-vframes", "1",
        "-q:v", "2",  # High quality (scale 2-31, lower = better quality)
        str(output_path),
    ]
    
    # Timeout: 2 minutes (should be quick, but allow for large/slow files)
    result = subprocess.run(
        ffmpeg_cmd,
        check=True,
        capture_output=True,
        timeout=120
    )
    
    # Verify thumbnail was created
    if not output_path.exists():
        raise FileNotFoundError(f"Thumbnail was not created at {output_path}")
    
    return output_path


def store_file(local_path: Path, storage_key: str) -> str:
    """
    Store file in local storage (Docker volume)
    
    Args:
        local_path: Path to source file
        storage_key: Storage path key (e.g., "{video_id}/video.mp4")
    
    Returns:
        URL path that backend can serve (e.g., "/uploads/processed/{video_id}/video.mp4")
    """
    try:
        # Store files in processed directory
        # Structure: processed/{video_id}/video.mp4
        #           processed/{video_id}/thumbnail.jpg
        local_storage = Path("/app/uploads/processed")
        local_storage.mkdir(parents=True, exist_ok=True)
        
        # Create destination path preserving directory structure
        dest_path = local_storage / storage_key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(local_path, dest_path)
        
        # Verify file was copied
        if not dest_path.exists():
            raise FileNotFoundError(f"Failed to copy file to {dest_path}")
        
        # Return a path that backend can serve (backend mounts /uploads)
        url_path = f"/uploads/processed/{storage_key}"
        print(f"  ✓ File stored: {dest_path} → {url_path}")
        return url_path
    except Exception as e:
        print(f"✗ ERROR storing file: {e}")
        import traceback
        traceback.print_exc()
        raise


# Register the task with multiple names to handle cross-app task sending
@celery_app.task(name="process_video", bind=True, max_retries=0)
def process_video(self, video_id: str, file_path: str):
    """
    Main video processing task with comprehensive error handling
    
    This task can be called from other Celery apps using:
    - send_task("process_video", ...) - simple name
    - send_task("worker.process_video", ...) - fully qualified name
    - send_task("short_video_platform.process_video", ...) - from backend app
    
    Args:
        video_id: UUID of the video record
        file_path: Path to the uploaded video file
    """
    # IMPORTANT: Print immediately to verify task is being called
    # Use both stdout and stderr, and flush immediately
    import sys
    try:
        print("="*60)
        print(f"TASK RECEIVED: process_video")
        print(f"Video ID: {video_id}")
        print(f"File path: {file_path}")
        print("="*60)
        sys.stdout.flush()
        
        print("="*60, file=sys.stderr)
        print(f"TASK RECEIVED: process_video", file=sys.stderr)
        print(f"Video ID: {video_id}", file=sys.stderr)
        print(f"File path: {file_path}", file=sys.stderr)
        print("="*60, file=sys.stderr)
        sys.stderr.flush()
    except Exception as e:
        print(f"ERROR in initial logging: {e}", file=sys.stderr)
        sys.stderr.flush()
    
    # Ensure file_path is absolute
    try:
        input_path = Path(file_path)
    except Exception as e:
        error_msg = f"Failed to create Path object: {e}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        sys.stderr.flush()
        raise
    if not input_path.is_absolute():
        # If relative, assume it's relative to /app/uploads/originals
        input_path = Path("/app/uploads/originals") / input_path
        print(f"⚠ Converted relative path to absolute: {input_path}")
    
    error_category = None
    user_friendly_error = None
    
    try:
        print(f"\n{'='*60}")
        print(f"📹 Starting video processing for {video_id}")
        print(f"{'='*60}")
        print(f"   Task received: process_video")
        print(f"   Video ID: {video_id}")
        print(f"   File path: {file_path}")
        print(f"   Absolute path: {input_path}")
        print(f"   File exists: {input_path.exists()}")
        if input_path.exists():
            print(f"   File size: {input_path.stat().st_size / 1024 / 1024:.2f} MB")
        else:
            print(f"   ⚠ WARNING: File does not exist at {input_path}")
        
        # Update status to processing (in case it wasn't already)
        update_video_status(video_id, "processing", error_reason=None)
        
        # Step 1: Get all video metadata in one ffprobe call
        print("  → Getting video metadata (format, duration, faststart check)...")
        metadata, metadata_error = get_video_metadata(input_path)
        if metadata_error:
            error_category = "VALIDATION_ERROR"
            user_friendly_error = f"Video file validation failed: {metadata_error}"
            print(f"✗ {user_friendly_error}")
            raise ValueError(metadata_error)
        
        # Validate metadata
        if metadata["duration"] <= 0:
            error_category = "VALIDATION_ERROR"
            user_friendly_error = "Video has invalid duration (0 or negative)"
            print(f"✗ {user_friendly_error}")
            raise ValueError(user_friendly_error)
        
        print(f"  ✓ Video metadata extracted:")
        print(f"     Format: {metadata['format_name']}")
        print(f"     Duration: {metadata['duration']:.2f} seconds")
        print(f"     Is MP4: {metadata['is_mp4']}")
        print(f"     Has faststart: {metadata['has_faststart']}")
        
        # Store duration for later use
        duration = metadata["duration"]
        is_mp4 = metadata["is_mp4"]
        has_faststart = metadata["has_faststart"]
        
        # Create output directory
        output_dir = TEMP_DIR / video_id
        output_dir.mkdir(exist_ok=True)
        
        # Step 2: Determine if transcoding is needed
        # Transcode if: not MP4, or MP4 without faststart
        needs_transcoding = not is_mp4 or (is_mp4 and not has_faststart)
        
        if not needs_transcoding:
            print("  ✓ File is already MP4 with faststart - no transcoding needed")
            # Copy file directly to output directory (no transcoding needed)
            mp4_path = output_dir / f"{video_id}.mp4"
            import shutil
            shutil.copy2(input_path, mp4_path)
            print("  ✓ MP4 file copied (transcoding skipped)")
        else:
            if is_mp4 and not has_faststart:
                print("  → File is MP4 but lacks faststart - transcoding to add faststart...")
            else:
                print("  → File is not MP4 - transcoding required...")
            
            # Transcode to MP4 (simple, universal format) with faststart
            mp4_path = output_dir / f"{video_id}.mp4"
            transcode_to_mp4(input_path, mp4_path)
            print("  ✓ MP4 transcoding complete (with faststart)")
        
        # Step 3: Create thumbnail
        print("  → Creating thumbnail...")
        thumbnail_path = output_dir / f"{video_id}_thumb.jpg"
        create_thumbnail(input_path, thumbnail_path)
        print("  ✓ Thumbnail created")
        
        # Step 4: Store processed files in local storage
        print("  → Storing processed files...")
        try:
            # Store MP4 file: processed/{video_id}/video.mp4
            mp4_url = store_file(mp4_path, f"{video_id}/video.mp4")
            
            # Store thumbnail: processed/{video_id}/thumbnail.jpg
            thumbnail_url = None
            if thumbnail_path and thumbnail_path.exists():
                thumbnail_url = store_file(thumbnail_path, f"{video_id}/thumbnail.jpg")
            
            print(f"  ✓ Storage complete (MP4 + thumbnail)")
        except Exception as e:
            error_category = "STORAGE_ERROR"
            user_friendly_error = "Failed to store processed video files."
            print(f"✗ ERROR during storage: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Step 5: Get detailed technical metadata from processed video
        # IMPORTANT: Extract metadata from the FINAL processed video file (mp4_path)
        # This works in both cases: transcoded OR copied - we analyze the final output file
        print("  → Extracting detailed video metadata from processed video...")
        
        # Initialize metadata dict
        detailed_metadata = {}
        
        # Verify mp4_path exists before extracting metadata
        if not mp4_path.exists():
            print(f"  ⚠ ERROR: Processed video file not found at {mp4_path}")
            detailed_metadata = {"error": "Processed video file not found"}
        else:
            detailed_metadata, metadata_error = get_detailed_video_metadata(mp4_path)
            
            # Ensure we always have a dict (never None)
            if detailed_metadata is None:
                print(f"  ⚠ Could not extract metadata: {metadata_error}")
                detailed_metadata = {"error": metadata_error or "Unknown error"}
            elif detailed_metadata:
                print(f"  ✓ Metadata extracted: {list(detailed_metadata.keys())}")
            else:
                print(f"  ⚠ Metadata extraction returned empty dict")
        
        # Step 6: Update database with processed video URLs and technical metadata
        update_data = {
            "url_mp4": mp4_url,
            "duration_seconds": int(duration),
            "error_reason": None,  # Clear any previous errors
        }
        
        if thumbnail_url:
            update_data["thumbnail"] = thumbnail_url
        
        # ALWAYS save metadata as JSON (even if empty dict or contains error)
        # This ensures video_metadata_json is never NULL in the database
        metadata_json = json.dumps(detailed_metadata, indent=2)
        update_data["video_metadata_json"] = metadata_json
        metadata_size = len(metadata_json)
        print(f"  → Saving technical metadata to database (JSON, {metadata_size} bytes)")
        if detailed_metadata and "error" not in detailed_metadata:
            print(f"     Metadata keys: {list(detailed_metadata.keys())}")
        else:
            print(f"     Warning: Metadata may be incomplete or contain errors")
        
        print(f"  → Updating database with processed video info")
        update_video_status(video_id, "ready", **update_data)
        
        print(f"✓ Video {video_id} processed successfully")
        print(f"  MP4 URL: {mp4_url}")
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

# Print startup information when module is imported
# This will run when Celery worker starts and imports this module
print("\n" + "="*60)
print("VIDEO WORKER MODULE LOADED")
print("="*60)
print(f"Celery app: {celery_app.main}")
print(f"Broker: {celery_app.conf.broker_url}")
print(f"Task routes configured for: process_video, worker.process_video, short_video_platform.process_video")
print("="*60 + "\n")

