# Migration Structure Review

## Current Issues

### 1. **001_initial_schema.sql** - Not Self-Contained
- Uses `\i ../schema.sql` which is path-dependent and not portable
- No transaction handling
- No rollback capability
- Not idempotent (will fail if run twice)

### 2. **002_visitor_analytics.sql** - Missing Best Practices
- ✅ Uses `IF NOT EXISTS` (good for idempotency)
- ❌ No transaction wrapper
- ❌ No migration tracking
- ❌ No rollback/down migration
- ❌ No error handling

### 3. **No Migration Tracking System**
- No table to track which migrations have been applied
- Can't prevent duplicate runs
- Can't track migration history

### 4. **Mixed Migration Approaches**
- Some in `database/migrations/`
- Some in `backend/migrations/`
- Some applied in code (`main.py`)
- Inconsistent execution method

## Recommended Improvements

### 1. Add Migration Tracking Table
```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Wrap Migrations in Transactions
```sql
BEGIN;
-- migration code
COMMIT;
```

### 3. Make Migrations Self-Contained
- Don't use `\i` to reference external files
- Include all necessary SQL in the migration file

### 4. Add Rollback/Down Migrations
- Create separate `*_down.sql` files for rollbacks
- Or include rollback logic in comments

### 5. Use Consistent Naming
- Format: `NNN_description.sql` (e.g., `001_initial_schema.sql`)
- Include both UP and DOWN migrations

### 6. Add Migration Runner Script
- Python script to apply migrations
- Checks which migrations have been applied
- Runs only new migrations
- Handles errors gracefully

