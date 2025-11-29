# Migration Instructions: Add error_reason Column

## Quick Fix

Run this command to add the `error_reason` column:

```bash
docker-compose exec postgres psql -U short5_user -d short5_db -c "ALTER TABLE videos ADD COLUMN error_reason TEXT;"
```

## Verify Column Exists

Check if the column was added:

```bash
docker-compose exec postgres psql -U short5_user -d short5_db -c "\d videos" | findstr error_reason
```

Or:

```bash
docker-compose exec postgres psql -U short5_user -d short5_db -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'videos' AND column_name = 'error_reason';"
```

## Alternative: Use the Python Script

```bash
docker-compose exec backend python scripts/add_error_reason_column.py
```

## After Migration

1. **Restart backend** to clear connection pool:
   ```bash
   docker-compose restart backend
   ```

2. **Verify it works** by checking a video:
   ```bash
   # This should work without errors
   curl http://localhost:8000/api/v1/users/me/videos
   ```

## If Still Getting Errors

1. Check backend logs:
   ```bash
   docker-compose logs backend --tail=50
   ```

2. Verify database connection:
   ```bash
   docker-compose exec backend python -c "from app.core.database import AsyncSessionLocal; import asyncio; from sqlalchemy import text; async def test(): async with AsyncSessionLocal() as db: await db.execute(text('SELECT 1')); print('DB connection OK'); asyncio.run(test())"
   ```

3. Check if you're using the correct database:
   ```bash
   docker-compose exec postgres psql -U short5_user -d short5_db -c "SELECT current_database();"
   ```

## Manual SQL (if needed)

Connect directly to PostgreSQL:

```bash
docker-compose exec postgres psql -U short5_user -d short5_db
```

Then run:

```sql
ALTER TABLE videos ADD COLUMN error_reason TEXT;
\q
```
