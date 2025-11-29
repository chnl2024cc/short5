# Video Error Handling and Cleanup System

## Overview

This document describes the comprehensive error handling, cleanup, and user notification system for video processing failures.

## Features

### 1. Video Validation
- **File Existence Check**: Verifies the uploaded file exists
- **File Size Check**: Ensures file is not empty
- **File Readability Check**: Verifies file permissions
- **Format Validation**: Uses FFprobe to validate video format and detect corruption
- **Duration Check**: Validates video has a valid duration

### 2. Error Categorization
Errors are categorized for better handling and user messaging:

- **VALIDATION_ERROR**: File validation failed (corrupted, invalid format, etc.)
- **TRANSCODING_ERROR**: FFmpeg transcoding failed
- **STORAGE_ERROR**: Failed to store processed files
- **METADATA_ERROR**: Could not extract video metadata
- **FILE_NOT_FOUND**: Video file was not found
- **UNKNOWN_ERROR**: Unexpected errors

### 3. User-Friendly Error Messages
Each error category has a user-friendly message:
- "Video file validation failed: [details]"
- "Video transcoding failed. The file may be corrupted or in an unsupported format."
- "Failed to store processed video files."
- "Could not extract video metadata."
- "Video file was not found. Please try uploading again."
- "An unexpected error occurred during video processing. Please try uploading again."

### 4. Automatic Cleanup
When a video fails, the system automatically:
- Deletes the original uploaded file
- Deletes processed files (HLS segments, playlists, thumbnails)
- Removes temporary processing directories
- Logs cleanup actions

### 5. Database Updates
- Sets video status to `failed`
- Stores error reason in `error_reason` field
- Updates `updated_at` timestamp

### 6. User Notification
Users can check video status via:
- **GET `/api/v1/videos/{video_id}`**: Returns video with `error_reason` if failed
- **GET `/api/v1/users/me/videos`**: Returns user's videos with error reasons
- **GET `/api/v1/users/me`**: Profile endpoint includes video stats

## Implementation Details

### Video Model Changes
Added `error_reason` field to store failure messages:
```python
error_reason = Column(Text)  # Store error message for failed videos
```

### Video Worker Process Flow

1. **Validation Phase**
   - Validates file exists, is readable, and not empty
   - Uses FFprobe to check format validity
   - Raises `VALIDATION_ERROR` if validation fails

2. **Transcoding Phase**
   - Transcodes video to HLS format
   - Catches FFmpeg errors and categorizes as `TRANSCODING_ERROR`
   - Continues even if thumbnail creation fails (non-critical)

3. **Storage Phase**
   - Uploads processed files to storage (S3/R2 or local)
   - Catches storage errors and categorizes as `STORAGE_ERROR`

4. **Metadata Phase**
   - Extracts video duration
   - Catches metadata extraction errors as `METADATA_ERROR`

5. **Error Handling Phase**
   - Categorizes errors
   - Generates user-friendly messages
   - Updates database with failure status and error reason
   - Cleans up all files
   - Returns error information (doesn't re-raise)

### Cleanup Function
```python
def cleanup_failed_video(video_id: str, file_path: Path):
    """Clean up files for a failed video"""
    # Removes:
    # - Original uploaded file
    # - Processed files in /app/uploads/processed/
    # - Temporary processing directory in /tmp/video_processing/
```

### API Response
Failed videos include `error_reason` in the response:
```json
{
  "id": "video-uuid",
  "status": "failed",
  "error_reason": "Video file validation failed: Video file is corrupted or invalid format",
  ...
}
```

## Usage

### For Users
1. Upload a video
2. Check video status via API endpoints
3. If status is `failed`, check `error_reason` for details
4. Re-upload if needed

### For Developers
1. Check video_worker logs for detailed error information
2. Error category is logged for debugging
3. Full traceback is logged for technical details
4. User-friendly message is stored in database

## Best Practices

1. **No Retries**: Videos that fail validation or are corrupted should not be retried automatically
2. **Immediate Cleanup**: Files are cleaned up immediately upon failure to save storage
3. **User-Friendly Messages**: Technical errors are translated to user-friendly messages
4. **Error Categorization**: Errors are categorized for better monitoring and debugging
5. **Non-Critical Failures**: Thumbnail failures don't stop processing
6. **Comprehensive Logging**: All errors are logged with full context

## Error Examples

### Validation Error
```
✗ Video file validation failed: Video file is corrupted or invalid format: Invalid data found when processing input
Error category: VALIDATION_ERROR
```

### Transcoding Error
```
✗ FFmpeg transcoding failed: [error details]
Error category: TRANSCODING_ERROR
```

### Storage Error
```
✗ ERROR during upload: [storage error]
Error category: STORAGE_ERROR
```

## Database Migration

To add the `error_reason` field, run:
```sql
ALTER TABLE videos ADD COLUMN error_reason TEXT;
```

Or use Alembic migration (recommended).
