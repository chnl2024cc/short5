#!/usr/bin/env python3
"""
Reprocess existing videos to generate MP4 files.

This script finds all READY videos that are missing url_mp4
and reprocesses them to generate MP4 files.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.video import Video, VideoStatus
from app.celery_app import celery_app


async def reprocess_videos_for_mp4():
    """Reprocess all videos that need MP4 conversion"""
    print("=" * 60)
    print("REPROCESSING VIDEOS FOR MP4")
    print("=" * 60)
    print()
    
    async with AsyncSessionLocal() as db:
        # Find videos that are READY but missing url_mp4
        # This includes videos that were processed but url_mp4 wasn't saved to DB
        result = await db.execute(
            select(Video).where(
                Video.status == VideoStatus.READY,
                (Video.url_mp4.is_(None) | Video.url_mp4 == "")
            )
        )
        videos = result.scalars().all()
        
        if not videos:
            print("✓ No videos need reprocessing")
            print("  All videos already have MP4 files")
            return
        
        print(f"Found {len(videos)} video(s) that need MP4 conversion")
        print()
        
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        for video in videos:
            print(f"Processing: {video.id}")
            print(f"  Title: {video.title or 'Untitled'}")
            print(f"  Status: {video.status.value}")
            print(f"  Current: url_mp4={video.url_mp4 is not None}")
            
            # Determine file path
            if video.original_filename:
                file_ext = Path(video.original_filename).suffix
            else:
                file_ext = ".mp4"  # Default
            
            file_path = Path(f"/app/uploads/originals/{video.id}{file_ext}")
            
            # Check if original file exists
            if not file_path.exists():
                print(f"  ⚠ Original file not found: {file_path}")
                print(f"  → Skipping (cannot reprocess without original file)")
                skipped_count += 1
                print()
                continue
            
            print(f"  ✓ Original file found: {file_path}")
            print(f"  → Sending to processing queue...")
            
            try:
                # Reset status to PROCESSING
                video.status = VideoStatus.PROCESSING
                video.error_reason = None
                await db.commit()
                
                # Send task to video worker
                result = celery_app.send_task(
                    "process_video",
                    args=[str(video.id), str(file_path)],
                    queue="celery",
                    ignore_result=True,
                )
                
                print(f"  ✓ Task queued: {result.id}")
                processed_count += 1
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                error_count += 1
                import traceback
                traceback.print_exc()
            
            print()
        
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  Queued for processing: {processed_count}")
        print(f"  Skipped (no file): {skipped_count}")
        print(f"  Errors: {error_count}")
        print(f"  Total: {len(videos)}")
        print()
        print("Monitor processing with:")
        print("  docker-compose logs -f video_worker")


if __name__ == "__main__":
    asyncio.run(reprocess_videos_for_mp4())
