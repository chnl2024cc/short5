"""
Force add error_reason column and verify
Run: docker-compose exec backend python scripts/fix_error_reason_column.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.core.database import AsyncSessionLocal, engine
from app.models.video import Video

async def fix_column():
    """Force add column and verify"""
    print("=" * 60)
    print("FIXING error_reason COLUMN")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Check if column exists in database
            print("\n1. Checking if column exists in database...")
            result = await db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'videos' 
                AND column_name = 'error_reason';
            """))
            exists = result.scalar_one_or_none()
            
            if exists:
                print("   ✓ Column exists in database")
            else:
                print("   ✗ Column does NOT exist. Adding it...")
                await db.execute(text("ALTER TABLE videos ADD COLUMN error_reason TEXT;"))
                await db.commit()
                print("   ✓ Column added to database")
            
            # Step 2: Test querying the column
            print("\n2. Testing column access...")
            test_result = await db.execute(text("SELECT error_reason FROM videos LIMIT 1;"))
            print("   ✓ Column is queryable")
            
            # Step 3: Check SQLAlchemy model
            print("\n3. Checking SQLAlchemy model...")
            if hasattr(Video, 'error_reason'):
                print("   ✓ Model has error_reason attribute")
            else:
                print("   ✗ Model missing error_reason attribute!")
            
            # Step 4: Test SQLAlchemy query
            print("\n4. Testing SQLAlchemy query...")
            from sqlalchemy import select
            result = await db.execute(select(Video).limit(1))
            video = result.scalar_one_or_none()
            if video:
                print(f"   ✓ SQLAlchemy can query Video model")
                print(f"   ✓ error_reason value: {video.error_reason}")
            else:
                print("   ⚠ No videos in database to test")
            
            print("\n" + "=" * 60)
            print("✓ ALL CHECKS PASSED - Column is ready!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_column())
