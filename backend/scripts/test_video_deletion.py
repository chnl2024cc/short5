"""
Test script for video deletion
Run: docker-compose exec backend python scripts/test_video_deletion.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.video import Video
from app.services.video_deletion import video_deletion_service


async def test_deletion():
    """Test video deletion service"""
    async with AsyncSessionLocal() as db:
        # Get first video
        result = await db.execute(select(Video).limit(1))
        video = result.scalar_one_or_none()
        
        if not video:
            print("No videos found in database")
            return
        
        print(f"Testing deletion for video: {video.id}")
        print(f"Video URLs: MP4={video.url_mp4}, Thumbnail={video.thumbnail}")
        
        try:
            deletion_result = await video_deletion_service.delete_video(
                str(video.id),
                db,
                video
            )
            
            print("\nDeletion Result:")
            print(f"  Database deleted: {deletion_result.get('database_deleted')}")
            print(f"  Storage deleted: {deletion_result.get('storage_deleted')}")
            print(f"  Errors: {deletion_result.get('errors')}")
            print(f"  Details: {deletion_result.get('storage_details')}")
            
            if deletion_result.get("database_deleted"):
                await db.commit()
                print("\n✓ Video deleted successfully!")
            else:
                await db.rollback()
                print("\n✗ Deletion failed!")
        except Exception as e:
            print(f"\n✗ Error during deletion: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(test_deletion())
