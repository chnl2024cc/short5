#!/usr/bin/env python3
"""
Fix videos that are ready but missing url_mp4 in database.

This script:
1. Finds videos with status=ready but url_mp4=null
2. Checks if the MP4 file actually exists on disk
3. Updates the database with the correct url_mp4 if file exists
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.video import Video, VideoStatus


async def fix_missing_url_mp4(video_id: str = None):
    """Fix videos missing url_mp4"""
    print("=" * 60)
    print("FIXING MISSING url_mp4")
    print("=" * 60)
    print()
    
    async with AsyncSessionLocal() as db:
        if video_id:
            # Fix specific video
            result = await db.execute(
                select(Video).where(Video.id == video_id)
            )
            videos = [result.scalar_one_or_none()] if result.scalar_one_or_none() else []
        else:
            # Find all videos that are ready but missing url_mp4
            result = await db.execute(
                select(Video).where(
                    Video.status == VideoStatus.READY,
                    (Video.url_mp4.is_(None) | Video.url_mp4 == "")
                )
            )
            videos = result.scalars().all()
        
        if not videos:
            print("✓ No videos need fixing")
            return
        
        print(f"Found {len(videos)} video(s) that need url_mp4 fix")
        print()
        
        fixed_count = 0
        skipped_count = 0
        
        for video in videos:
            print(f"Checking: {video.id}")
            print(f"  Title: {video.title or 'Untitled'}")
            print(f"  Status: {video.status.value}")
            print(f"  Current url_mp4: {video.url_mp4}")
            
            # Check if MP4 file exists
            mp4_path = Path(f"/app/uploads/processed/{video.id}/video.mp4")
            print(f"  Expected MP4 path: {mp4_path}")
            print(f"  File exists: {mp4_path.exists()}")
            
            if mp4_path.exists():
                # File exists! Update database
                expected_url = f"/uploads/processed/{video.id}/video.mp4"
                print(f"  → Updating database with url_mp4: {expected_url}")
                
                try:
                    # Use raw SQL to update
                    update_query = text("""
                        UPDATE videos 
                        SET url_mp4 = :url_mp4, updated_at = CURRENT_TIMESTAMP
                        WHERE id = CAST(:video_id AS uuid)
                    """)
                    await db.execute(
                        update_query,
                        {"url_mp4": expected_url, "video_id": str(video.id)}
                    )
                    await db.commit()
                    
                    print(f"  ✓ Database updated successfully")
                    fixed_count += 1
                except Exception as e:
                    print(f"  ✗ Error updating database: {e}")
                    await db.rollback()
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  ⚠ MP4 file not found - video needs to be reprocessed")
                print(f"  → Run: docker-compose exec backend python scripts/reprocess_videos_for_mp4.py")
                skipped_count += 1
            
            print()
        
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  Fixed: {fixed_count}")
        print(f"  Need reprocessing: {skipped_count}")
        print(f"  Total: {len(videos)}")


if __name__ == "__main__":
    video_id = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(fix_missing_url_mp4(video_id))

