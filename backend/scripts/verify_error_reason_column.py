"""
Script to verify and add error_reason column to videos table
Run: docker-compose exec backend python scripts/verify_error_reason_column.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def verify_and_add_column():
    """Verify error_reason column exists, add it if it doesn't"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if column exists
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'videos' 
                    AND column_name = 'error_reason'
                ) AS column_exists;
            """))
            exists = result.scalar()
            
            if exists:
                print("✓ Column 'error_reason' already exists in videos table")
            else:
                print("✗ Column 'error_reason' does not exist. Adding it...")
                await db.execute(text("ALTER TABLE videos ADD COLUMN error_reason TEXT;"))
                await db.commit()
                print("✓ Column 'error_reason' added successfully")
            
            # Verify by trying to query it
            test_result = await db.execute(text("SELECT error_reason FROM videos LIMIT 1;"))
            print("✓ Column is accessible and queryable")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(verify_and_add_column())
