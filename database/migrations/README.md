# Database Migrations

## Structure

Migrations are numbered sequentially and should be applied in order:

- `000_migration_tracking.sql` - Creates migration tracking table (run first)
- `001_initial_schema.sql` - Initial database schema
- `002_visitor_analytics.sql` - Visitor analytics tracking

## Single Source of Truth

**Migrations are the single source of truth** for database schema. The `schema.sql` file in the parent directory simply runs these migrations in order for convenience.

## Best Practices

1. **Idempotent**: All migrations use `IF NOT EXISTS` and can be run multiple times safely
2. **Transactional**: Each migration is wrapped in `BEGIN`/`COMMIT`
3. **Self-contained**: No external file dependencies
4. **Tracked**: Migrations are recorded in `schema_migrations` table
5. **Single source of truth**: Schema changes should be made in migrations, not in schema.sql

## Running Migrations

### Manual Execution

```bash
# Run all migrations in order
psql -U short5_user -d short5_db -f database/migrations/000_migration_tracking.sql
psql -U short5_user -d short5_db -f database/migrations/001_initial_schema.sql
psql -U short5_user -d short5_db -f database/migrations/002_visitor_analytics.sql
```

### Docker Execution

```bash
# Run migration
docker exec -i short5_postgres psql -U short5_user -d short5_db < database/migrations/002_visitor_analytics.sql
```

### Using Migration Runner (Recommended)

```bash
python database/migrations/run_migrations.py
```

## Creating New Migrations

1. Create file: `database/migrations/XXX_description.sql`
2. Use sequential numbering (003, 004, etc.)
3. Wrap in transaction: `BEGIN; ... COMMIT;`
4. Use `IF NOT EXISTS` for idempotency
5. Update this README

## Rollback

Currently, migrations don't include rollback scripts. To rollback:
1. Manually reverse the changes
2. Remove entry from `schema_migrations` table
3. Or create a new migration to undo changes

## Migration Tracking

Check which migrations have been applied:

```sql
SELECT * FROM schema_migrations ORDER BY applied_at;
```

