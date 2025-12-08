#!/usr/bin/env python3
"""
Migration Runner Script
Applies database migrations in order, tracking which have been applied.
"""
import os
import sys
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://short5_user:short5_password@localhost:5432/short5_db"
)


async def get_applied_migrations(conn):
    """Get list of already applied migrations"""
    try:
        rows = await conn.fetch("SELECT version FROM schema_migrations ORDER BY version")
        return {row['version'] for row in rows}
    except asyncpg.UndefinedTableError:
        # Migration tracking table doesn't exist yet
        return set()


async def record_migration(conn, version, description, checksum=None, execution_time_ms=None):
    """Record that a migration has been applied"""
    await conn.execute(
        """
        INSERT INTO schema_migrations (version, description, checksum, execution_time_ms)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (version) DO NOTHING
        """,
        version, description, checksum, execution_time_ms
    )


def calculate_checksum(file_path):
    """Calculate SHA256 checksum of migration file"""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


async def run_migration(conn, migration_file):
    """Run a single migration file"""
    migration_path = Path(migration_file)
    version = migration_path.stem  # e.g., "001_initial_schema"
    
    print(f"Running migration: {version}...")
    
    start_time = datetime.now()
    
    # Read migration file
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Calculate checksum
    checksum = calculate_checksum(migration_path)
    
    # Execute migration
    try:
        await conn.execute(sql)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Extract description from SQL comments
        description = "Migration"
        for line in sql.split('\n'):
            if 'Description:' in line:
                description = line.split('Description:')[1].strip()
                break
        
        # Record migration
        await record_migration(conn, version, description, checksum, int(execution_time_ms))
        
        print(f"✓ Migration {version} applied successfully ({execution_time:.0f}ms)")
        return True
    except Exception as e:
        print(f"✗ Migration {version} failed: {e}")
        return False


async def main():
    """Main migration runner"""
    migrations_dir = Path(__file__).parent
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("No migration files found!")
        return
    
    print(f"Found {len(migration_files)} migration file(s)")
    
    # Connect to database
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("Connected to database")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return
    
    try:
        # Get applied migrations
        applied = await get_applied_migrations(conn)
        print(f"Found {len(applied)} already applied migration(s)")
        
        # Run migrations in order
        for migration_file in migration_files:
            version = migration_file.stem
            
            # Skip migration tracking migration if table doesn't exist
            if version == "000_migration_tracking" and len(applied) == 0:
                # First run - need to create tracking table
                await run_migration(conn, migration_file)
                applied.add(version)
                continue
            
            # Skip if already applied
            if version in applied:
                print(f"⊘ Migration {version} already applied, skipping")
                continue
            
            # Run migration
            success = await run_migration(conn, migration_file)
            if not success:
                print("Migration failed. Stopping.")
                return
            
            applied.add(version)
        
        print("\n✓ All migrations completed successfully!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

