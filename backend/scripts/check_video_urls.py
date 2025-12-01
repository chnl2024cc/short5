"""
Diagnostic script to check video URLs and accessibility
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.video import Video
from app.core.config import settings
import httpx

async def check_video(video_id: str = None):
    """Check video URLs and accessibility"""
    # Database connection
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        if video_id:
            result = await db.execute(select(Video).where(Video.id == video_id))
            videos = [result.scalar_one_or_none()] if result.scalar_one_or_none() else []
        else:
            # Get all ready videos
            result = await db.execute(select(Video).where(Video.status == "ready"))
            videos = result.scalars().all()
        
        if not videos:
            print("No videos found")
            return
        
        print(f"\n{'='*80}")
        print(f"Checking {len(videos)} video(s)")
        print(f"{'='*80}\n")
        
        for video in videos:
            print(f"Video ID: {video.id}")
            print(f"Status: {video.status}")
            print(f"Title: {video.title or 'Untitled'}")
            print(f"\nURLs:")
            print(f"  url_mp4: {video.url_mp4}")
            print(f"  thumbnail: {video.thumbnail}")
            
            # Check if URLs are accessible
            base_url = "http://localhost:8000"
            
            if video.url_mp4:
                print(f"\n  Checking MP4 URL...")
                if video.url_mp4.startswith("/"):
                    test_url = f"{base_url}{video.url_mp4}"
                else:
                    test_url = video.url_mp4
                
                print(f"    Full URL: {test_url}")
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.head(test_url)
                        print(f"    Status: {response.status_code}")
                        if response.status_code == 200:
                            print(f"    ✓ MP4 is accessible")
                        else:
                            print(f"    ✗ MP4 returned {response.status_code}")
                except Exception as e:
                    print(f"    ✗ Error accessing MP4 URL: {e}")
            
            if video.thumbnail:
                print(f"\n  Checking thumbnail URL...")
                if video.thumbnail.startswith("/"):
                    test_url = f"{base_url}{video.thumbnail}"
                else:
                    test_url = video.thumbnail
                
                print(f"    Full URL: {test_url}")
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.head(test_url)
                        print(f"    Status: {response.status_code}")
                        if response.status_code == 200:
                            print(f"    ✓ Thumbnail is accessible")
                        else:
                            print(f"    ✗ Thumbnail returned {response.status_code}")
                except Exception as e:
                    print(f"    ✗ Error accessing thumbnail URL: {e}")
            
            # Check if files exist on disk (for local storage)
            if video.url_mp4 and video.url_mp4.startswith("/uploads/processed"):
                # New structure: /uploads/processed/{video_id}/video.mp4
                file_path = Path(f"/app/uploads/processed/{video.url_mp4.replace('/uploads/processed/', '')}")
                print(f"\n  Local file check (MP4):")
                print(f"    Expected path: {file_path}")
                print(f"    File exists: {file_path.exists()}")
                if file_path.exists():
                    print(f"    File size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
            
            print(f"\n{'-'*80}\n")
    
    await engine.dispose()

if __name__ == "__main__":
    video_id = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(check_video(video_id))
