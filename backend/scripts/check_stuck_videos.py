"""
Check videos stuck in processing status
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.core.config import settings
from app.models.video import Video, VideoStatus


async def check_stuck_videos():
    """Check for videos stuck in processing"""
    # Ensure DATABASE_URL uses asyncpg driver for async operations
    database_url = settings.DATABASE_URL
    print(f"Original DATABASE_URL: {database_url[:50]}...")  # Debug output
    
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgresql+psycopg2://"):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    elif not database_url.startswith("postgresql+asyncpg://"):
        # If it's already asyncpg, keep it; otherwise convert
        if "postgresql" in database_url:
            database_url = database_url.replace("postgresql", "postgresql+asyncpg", 1)
    
    print(f"Using DATABASE_URL: {database_url[:50]}...")  # Debug output
    
    try:
        engine = create_async_engine(database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    except Exception as e:
        print(f"✗ ERROR creating database engine: {e}")
        print(f"  DATABASE_URL: {database_url}")
        raise
    
    async with async_session() as session:
        # Find videos stuck in processing for more than 5 minutes
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        result = await session.execute(
            select(Video)
            .where(
                Video.status == VideoStatus.PROCESSING,
                Video.updated_at < cutoff_time
            )
            .order_by(Video.created_at.desc())
        )
        stuck_videos = result.scalars().all()
        
        print(f"\n{'='*60}")
        print(f"STUCK VIDEOS CHECK")
        print(f"{'='*60}\n")
        
        if not stuck_videos:
            print("✅ No videos stuck in processing status")
            print("   (All processing videos are recent or completed)")
        else:
            print(f"⚠️  Found {len(stuck_videos)} video(s) stuck in PROCESSING:\n")
            
            for video in stuck_videos:
                age_minutes = (datetime.now(timezone.utc) - video.updated_at).total_seconds() / 60
                print(f"  Video ID: {video.id}")
                print(f"  Title: {video.title or 'Untitled'}")
                print(f"  Status: {video.status.value}")
                print(f"  Created: {video.created_at}")
                print(f"  Last Updated: {video.updated_at} ({age_minutes:.1f} minutes ago)")
                print(f"  Error Reason: {video.error_reason or 'None'}")
                print(f"  File: {video.original_filename}")
                print()
        
        # Also check all processing videos
        all_processing = await session.execute(
            select(Video).where(Video.status == VideoStatus.PROCESSING)
        )
        all_processing_videos = all_processing.scalars().all()
        
        if all_processing_videos:
            print(f"\n📊 All videos in PROCESSING status: {len(all_processing_videos)}\n")
            for video in all_processing_videos:
                age_minutes = (datetime.now(timezone.utc) - video.updated_at).total_seconds() / 60
                print(f"  - {video.id} ({age_minutes:.1f} min ago)")
        
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_stuck_videos())
