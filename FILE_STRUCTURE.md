# File Structure

## Overview
Clear, logical file structure for video storage.

## Directory Structure

```
/app/uploads/
├── originals/                    # Original uploaded files (as received)
│   └── {video_id}.mp4           # Original file from user
│
└── processed/                    # Processed files (ready for serving)
    └── {video_id}/
        ├── video.mp4            # Processed MP4 (web-optimized)
        └── thumbnail.jpg        # Video thumbnail
```

## Path Details

### Original Files
- **Location:** `/app/uploads/originals/{video_id}.{ext}`
- **Purpose:** Store original uploaded file as-is
- **Example:** `/app/uploads/originals/635614c3-935f-4b10-8fbf-b51e697e0ac4.mp4`

### Processed Files
- **MP4:** `/app/uploads/processed/{video_id}/video.mp4`
- **Thumbnail:** `/app/uploads/processed/{video_id}/thumbnail.jpg`
- **URLs:** 
  - MP4: `http://localhost:8000/uploads/processed/{video_id}/video.mp4`
  - Thumbnail: `http://localhost:8000/uploads/processed/{video_id}/thumbnail.jpg`

## Benefits

✅ **Clear separation:** Originals vs processed files
✅ **Organized:** All files for a video in one directory
✅ **Simple naming:** `video.mp4` and `thumbnail.jpg` (not `{video_id}.mp4`)
✅ **Short paths:** `processed/{video_id}/` (no redundant `videos/` subdirectory)
✅ **Easy to find:** Everything for a video is in `processed/{video_id}/`
✅ **Easy to delete:** Delete entire `{video_id}` directory to remove all files

## File Flow

1. **Upload:** User uploads → Saved to `originals/{video_id}.mp4`
2. **Process:** Worker reads from `originals/` → Transcodes → Saves to `processed/{video_id}/`
3. **Serve:** Backend serves from `processed/` via `/uploads/processed/...` endpoint

## Notes

- Original files are kept for reprocessing if needed
- Processed files are what users actually see/play
- All processed files for a video are in one directory for easy management
