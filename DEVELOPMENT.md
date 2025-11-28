# Development Guide

## Development Workflow

### Setting Up Development Environment

1. **Clone and setup**
   ```bash
   git clone <repo>
   cd short5_swiper_bugagaa
   cp .env.example .env
   ```

2. **Start infrastructure services**
   ```bash
   docker-compose up -d postgres redis
   ```

3. **Run backend locally**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

4. **Run frontend locally**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Code Style

### Backend (Python)

- Use **Black** for code formatting
- Use **Ruff** for linting
- Follow PEP 8 style guide
- Type hints are required for all functions

```bash
# Format code
black backend/

# Lint code
ruff check backend/
```

### Frontend (TypeScript/Vue)

- Use **ESLint** for linting
- Follow Vue 3 style guide
- Use Composition API with `<script setup>`
- TypeScript strict mode enabled

```bash
# Lint code
npm run lint

# Type check
npm run typecheck
```

## Database Migrations

### Using Alembic

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Manual SQL

For schema changes, update `database/schema.sql` and create a migration file in `database/migrations/`.

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## API Development

### Adding New Endpoints

1. Create route file in `backend/app/api/v1/`
2. Define Pydantic models for request/response
3. Add route to `backend/app/api/v1/router.py`
4. Update `API_SPEC.md` with endpoint documentation

### Example Endpoint

```python
# backend/app/api/v1/example.py
from fastapi import APIRouter, Depends
from app.core.database import get_db

router = APIRouter()

@router.get("/example")
async def example_endpoint(db: AsyncSession = Depends(get_db)):
    return {"message": "Hello"}
```

## Frontend Development

### Adding New Components

1. Create component in `frontend/components/`
2. Use Composition API with `<script setup>`
3. Add TypeScript types
4. Use Pinia stores for state management

### Example Component

```vue
<template>
  <div>{{ message }}</div>
</template>

<script setup lang="ts">
interface Props {
  message: string
}

defineProps<Props>()
</script>
```

## Video Processing

### Testing Video Worker Locally

```bash
cd video_worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="..."
export REDIS_URL="..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export S3_BUCKET_NAME="..."

# Start Celery worker
celery -A worker worker --loglevel=info
```

### Processing a Video

```python
from video_worker.worker import process_video

result = process_video.delay(video_id="uuid", file_path="/path/to/video.mp4")
```

## Debugging

### Backend

- Use `print()` or `logging` for debugging
- FastAPI auto-reloads on code changes
- Check logs: `docker-compose logs backend`

### Frontend

- Use Vue DevTools browser extension
- Check browser console
- Nuxt DevTools available at `/__nuxt_devtools__`

### Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U short5_user -d short5_db

# View tables
\dt

# Query data
SELECT * FROM videos LIMIT 10;
```

### Redis

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# View keys
KEYS *

# View queue
LLEN celery
```

## Common Issues

### Database Connection Errors

- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running: `docker-compose ps postgres`
- Check database exists: `docker-compose exec postgres psql -U short5_user -l`

### Redis Connection Errors

- Check `REDIS_URL` in `.env`
- Ensure Redis is running: `docker-compose ps redis`
- Test connection: `docker-compose exec redis redis-cli ping`

### Video Processing Fails

- Check FFmpeg is installed in video_worker container
- Verify S3 credentials and bucket permissions
- Check video file format is supported
- Review worker logs: `docker-compose logs video_worker`

### Frontend API Errors

- Check `NUXT_PUBLIC_API_BASE_URL` is correct
- Verify CORS settings in backend
- Check browser network tab for request details

## Performance Optimization

### Database

- Add indexes for frequently queried columns
- Use connection pooling
- Monitor slow queries

### Frontend

- Implement video preloading (1-2 videos ahead)
- Lazy load components
- Optimize images and assets
- Use CDN for static assets

### Video Processing

- Use multiple Celery workers for parallel processing
- Optimize FFmpeg encoding settings
- Cache transcoded videos
- Use CDN for video delivery

## Deployment

### Production Checklist

- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Configure production database
- [ ] Set up S3/R2 bucket with proper permissions
- [ ] Configure CORS for production domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline

### Environment Variables for Production

```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host:5432/db
JWT_SECRET_KEY=<strong-random-key>
AWS_ACCESS_KEY_ID=<production-key>
AWS_SECRET_ACCESS_KEY=<production-secret>
S3_BUCKET_NAME=<production-bucket>
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Nuxt 4 Documentation](https://nuxt.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

