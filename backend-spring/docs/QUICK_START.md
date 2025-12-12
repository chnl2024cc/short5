# Spring Boot Backend - Quick Start Guide

## Summary

✅ **Yes, you can still use all existing services!**

The Spring Boot backend is designed to work alongside the FastAPI backend, sharing the same infrastructure:

- ✅ **PostgreSQL** - Same database, both backends can use it
- ✅ **Redis** - Same Redis instance for caching and task queue
- ✅ **video_worker** - Can still be used! Spring Boot can send tasks to it
- ✅ **File Storage** - Same `/app/uploads` directory structure

## What Has Been Created

### 1. Migration Analysis
- [MIGRATION.md](MIGRATION.md) - Complete migration plan and analysis

### 2. Spring Boot Project Structure
```
backend-spring/
├── pom.xml                    # Maven dependencies
├── Dockerfile                 # Docker build
├── src/main/
│   ├── java/com/short5/
│   │   ├── Short5Application.java  # Main application
│   │   ├── config/            # Configuration classes
│   │   │   ├── DatabaseConfig.java
│   │   │   ├── CorsConfig.java
│   │   │   ├── RedisConfig.java
│   │   │   └── FileStorageConfig.java
│   │   ├── controller/       # REST controllers (TODO)
│   │   ├── service/          # Business logic (TODO)
│   │   ├── repository/        # Data access (TODO)
│   │   ├── entity/            # JPA entities (TODO)
│   │   └── security/          # JWT auth (TODO)
│   └── resources/
│       └── application.yml    # Configuration
└── README.md
```

### 3. Configuration Files
- ✅ Maven `pom.xml` with all dependencies
- ✅ `application.yml` with database, Redis, JWT config
- ✅ Docker configuration
- ✅ CORS, file storage, Redis setup

## Integration with Existing Services

### PostgreSQL Database
```yaml
# Spring Boot uses the same database
spring:
  datasource:
    url: jdbc:postgresql://postgres:5432/short5_db
    username: ${POSTGRES_USER}
    password: ${POSTGRES_PASSWORD}
```

### Redis
```yaml
# Same Redis instance
spring:
  data:
    redis:
      host: redis
      port: 6379
```

### video_worker Integration

**Option 1: HTTP Bridge (Recommended)**
- Spring Boot calls FastAPI endpoint: `POST /api/v1/internal/tasks/process_video`
- FastAPI sends task to Celery
- No changes needed to video_worker

**Option 2: Direct Redis/Celery Protocol**
- Spring Boot sends tasks directly to Redis using Celery protocol
- Requires Java Celery client library (may need to find/create one)

**Option 3: Keep FastAPI Running**
- Spring Boot calls FastAPI for video processing
- Both backends run simultaneously
- Frontend can use either backend

## Running Spring Boot Backend

### Option 1: Docker Compose (Recommended)

Add to your `docker-compose.yml`:

```yaml
services:
  # ... existing services (postgres, redis, video_worker, backend) ...
  
  backend-spring:
    build:
      context: ./backend-spring
      dockerfile: Dockerfile
    container_name: short5_backend_spring
    environment:
      DATABASE_URL: jdbc:postgresql://postgres:5432/short5_db
      POSTGRES_USER: ${POSTGRES_USER:-short5_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-short5_password}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-change-me-in-production}
      UPLOAD_DIR: /app/uploads
      SPRING_BACKEND_PORT: 8080
      CELERY_BROKER_URL: ${CELERY_BROKER_URL:-redis://redis:6379/0}
    ports:
      - "${SPRING_BACKEND_PORT:-8080}:8080"
    volumes:
      - backend_uploads:/app/uploads  # Same volume as FastAPI backend
      - ./geodata:/app/geodata:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - short5_network
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 40s
```

Then run:
```bash
docker-compose up -d backend-spring
```

### Option 2: Local Development

```bash
cd backend-spring
mvn clean package
java -jar target/short5-backend-spring-1.0.0.jar
```

## What's Next?

The Spring Boot backend structure is set up, but the following still need to be implemented:

### High Priority
1. **JPA Entity Models** - Map from SQLAlchemy models
2. **Repository Layer** - Spring Data JPA repositories
3. **JWT Authentication Service** - Token generation/validation
4. **REST Controllers** - All API endpoints
5. **Service Layer** - Business logic

### Medium Priority
6. **File Upload Service** - Handle video uploads
7. **Feed/Recommendation Service** - Algorithm implementation
8. **Video Processing Integration** - Connect to video_worker
9. **Exception Handling** - Global exception handlers

### Low Priority
10. **Unit Tests** - Service and controller tests
11. **Integration Tests** - End-to-end API tests
12. **Documentation** - API documentation (Swagger/OpenAPI)

## Port Configuration

- **FastAPI Backend**: Port `8000` (default)
- **Spring Boot Backend**: Port `8080` (default)
- Both can run simultaneously on different ports

## Frontend Configuration

The frontend can be configured to use either backend:

```typescript
// Use FastAPI backend
const API_BASE_URL = 'http://localhost:8000/api/v1'

// Or use Spring Boot backend
const API_BASE_URL = 'http://localhost:8080/api/v1'
```

## Questions Answered

### Q: Can we still use video_worker?
**A: Yes!** Spring Boot can send tasks to the existing video_worker via:
- HTTP bridge (FastAPI endpoint)
- Direct Redis/Celery protocol
- Keep FastAPI running as task gateway

### Q: Can we still use Redis?
**A: Yes!** Spring Boot uses the same Redis instance for:
- Caching
- Session storage (if needed)
- Task queue communication

### Q: Can we still use PostgreSQL?
**A: Yes!** Spring Boot uses the same database. Both backends can read/write to the same tables.

### Q: Can both backends run simultaneously?
**A: Yes!** They use different ports and can coexist. You can:
- Run both for testing/comparison
- Use one in production
- Load balance between them

## Next Steps

1. Review the migration plan: [MIGRATION.md](MIGRATION.md)
2. Start implementing entities (see existing SQLAlchemy models)
3. Implement authentication endpoints first
4. Gradually migrate other endpoints
5. Test integration with existing services

## Support

For questions or issues, refer to:
- [MIGRATION.md](MIGRATION.md) - Detailed migration plan
- [README.md](../README.md) - Spring Boot specific docs
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide and best practices
- [API.md](API.md) - Complete API documentation

