# Spring Boot Backend Migration Analysis

## Executive Summary

This document outlines the migration plan for adding Spring Boot as an additional, optionally usable backend alongside the existing FastAPI backend. The migration is designed to be **non-disruptive** - both backends can coexist and use the same infrastructure.

## Current Architecture

### FastAPI Backend (Python)
- **Framework**: FastAPI with async SQLAlchemy
- **Database**: PostgreSQL (asyncpg driver)
- **Message Broker**: Redis (via Celery)
- **Task Processing**: Celery workers (video_worker)
- **Authentication**: JWT tokens
- **File Storage**: Local Docker volumes (`/app/uploads`)

### Services Used
1. **PostgreSQL** - Primary database
2. **Redis** - Celery broker/backend
3. **video_worker** - Separate Python service for video processing (FFmpeg)
4. **Static File Serving** - FastAPI serves `/uploads` directory

## Migration Strategy

### ✅ Services That Can Be Reused

All existing services can be reused with Spring Boot:

1. **PostgreSQL Database** ✅
   - Spring Boot will use the same database
   - JPA/Hibernate will map to existing tables
   - Both backends can read/write to the same database

2. **Redis** ✅
   - Spring Boot can use Redis for:
     - Caching (Spring Cache with Redis)
     - Session storage (if needed)
     - **Celery task integration** (send tasks to existing video_worker)
   - Spring Boot can send Celery tasks via Redis using Celery's protocol

3. **video_worker** ✅
   - **Can still be used!** Spring Boot can send tasks to Celery via Redis
   - No changes needed to video_worker
   - Spring Boot will use Celery's task protocol to communicate

4. **File Storage** ✅
   - Same `/app/uploads` directory structure
   - Spring Boot can serve static files from the same location
   - Both backends can access the same files

### Architecture Options

#### Option 1: Spring Boot + Celery Integration (Recommended)
- Spring Boot sends video processing tasks to existing Celery workers
- Uses Redis as message broker
- **Pros**: No changes to video_worker, reuse existing infrastructure
- **Cons**: Requires Celery client library for Java (or HTTP bridge)

#### Option 2: Spring Boot + Spring Async
- Replace Celery with Spring's async processing
- Use Redis for task queue
- **Pros**: Pure Java/Spring solution
- **Cons**: Requires rewriting video processing logic in Java

#### Option 3: Hybrid Approach
- Spring Boot for API endpoints
- Keep video_worker as-is (Python/Celery)
- Use HTTP API or Redis pub/sub for communication
- **Pros**: Best of both worlds
- **Cons**: More complex integration

**Recommendation**: Option 1 or 3 - Keep video_worker as-is and integrate via Redis/Celery protocol.

## Migration Checklist

### Phase 1: Project Setup
- [x] Create Spring Boot project structure
- [ ] Configure Maven/Gradle build
- [ ] Set up package structure
- [ ] Configure application.properties/yml

### Phase 2: Core Infrastructure
- [ ] Database configuration (PostgreSQL)
- [ ] JPA/Hibernate entities (map from SQLAlchemy models)
- [ ] Repository layer (Spring Data JPA)
- [ ] Redis configuration
- [ ] JWT authentication setup
- [ ] CORS configuration
- [ ] Static file serving

### Phase 3: API Endpoints
- [ ] Authentication endpoints (`/api/v1/auth/*`)
- [ ] User endpoints (`/api/v1/users/*`)
- [ ] Video endpoints (`/api/v1/videos/*`)
- [ ] Feed endpoints (`/api/v1/feed`)
- [ ] Report endpoints (`/api/v1/reports/*`)
- [ ] Admin endpoints (`/api/v1/admin/*`)
- [ ] Analytics endpoints (`/api/v1/admin/shares`, `/api/v1/admin/visitors`)

### Phase 4: Services & Business Logic
- [ ] User service
- [ ] Video service
- [ ] Feed/recommendation service
- [ ] Authentication service
- [ ] File upload service
- [ ] Video processing integration (Celery/Redis)

### Phase 5: Integration
- [ ] Celery task client (for video_worker)
- [ ] Redis integration
- [ ] File storage integration
- [ ] GeoIP service (visitor analytics)

### Phase 6: Testing & Deployment
- [ ] Unit tests
- [ ] Integration tests
- [ ] Docker configuration
- [ ] Docker Compose integration
- [ ] Environment configuration

## Technical Details

### Database Models to Migrate

1. **User** (`users` table)
2. **Video** (`videos` table)
3. **Vote** (`votes` table)
4. **View** (`views` table)
5. **UserLikedVideo** (`user_liked_videos` table)
6. **Report** (`reports` table)
7. **ShareLink** (`share_links` table)
8. **ShareClick** (`share_clicks` table)
9. **VisitorLog** (`visitor_logs` table)

### API Endpoints to Implement

#### Authentication (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /refresh` - Refresh token
- `POST /logout` - User logout

#### Users (`/api/v1/users`)
- `GET /me` - Get current user profile
- `GET /{user_id}/videos` - Get user's videos

#### Videos (`/api/v1/videos`)
- `GET /{video_id}` - Get video details
- `POST /upload` - Upload video
- `DELETE /{video_id}` - Delete video
- `POST /{video_id}/vote` - Vote on video
- `POST /{video_id}/view` - Record view
- `POST /{video_id}/share` - Share video
- `POST /{video_id}/share/click` - Track share click
- `POST /{video_id}/like` - Like video (save)
- `DELETE /{video_id}/like` - Unlike video

#### Feed (`/api/v1/feed`)
- `GET /` - Get personalized feed

#### Reports (`/api/v1/reports`)
- `POST /` - Create report

#### Admin (`/api/v1/admin`)
- `GET /videos` - List all videos
- `POST /videos/{video_id}/approve` - Approve video
- `POST /videos/{video_id}/reject` - Reject video
- `GET /reports` - List reports
- `POST /reports/{report_id}/resolve` - Resolve report

#### Analytics (`/api/v1/admin/shares`, `/api/v1/admin/visitors`)
- `GET /admin/shares` - Share analytics
- `GET /admin/visitors` - Visitor analytics

### Dependencies Needed

```xml
<!-- Spring Boot Starter Web -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>

<!-- Spring Data JPA -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>

<!-- PostgreSQL Driver -->
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
</dependency>

<!-- Redis -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>

<!-- JWT -->
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-api</artifactId>
    <version>0.12.3</version>
</dependency>
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-impl</artifactId>
    <version>0.12.3</version>
</dependency>
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-jackson</artifactId>
    <version>0.12.3</version>
</dependency>

<!-- File Upload -->
<dependency>
    <groupId>commons-fileupload</groupId>
    <artifactId>commons-fileupload</artifactId>
    <version>1.5</version>
</dependency>

<!-- GeoIP (MaxMind) -->
<dependency>
    <groupId>com.maxmind.geoip2</groupId>
    <artifactId>geoip2</artifactId>
    <version>4.3.1</version>
</dependency>

<!-- Celery Client (for video_worker integration) -->
<!-- Note: May need to use HTTP bridge or direct Redis protocol -->
```

### Configuration Files

#### `application.yml`
```yaml
spring:
  datasource:
    url: ${DATABASE_URL:jdbc:postgresql://localhost:5432/short5_db}
    username: ${POSTGRES_USER:short5_user}
    password: ${POSTGRES_PASSWORD:short5_password}
    driver-class-name: org.postgresql.Driver
  
  jpa:
    hibernate:
      ddl-auto: validate  # Don't auto-create tables (use existing schema)
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true
  
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      password: ${REDIS_PASSWORD:}
  
  servlet:
    multipart:
      max-file-size: 500MB
      max-request-size: 500MB

jwt:
  secret: ${JWT_SECRET_KEY:change-me-in-production}
  algorithm: ${JWT_ALGORITHM:HS256}
  access-token-expire-minutes: ${JWT_ACCESS_TOKEN_EXPIRE_MINUTES:30}
  refresh-token-expire-days: ${JWT_REFRESH_TOKEN_EXPIRE_DAYS:7}

cors:
  allowed-origins: ${CORS_ORIGINS:http://localhost:3000,http://localhost:8080,http://localhost:5173}

file:
  upload-dir: ${UPLOAD_DIR:/app/uploads}
  max-size: ${MAX_UPLOAD_SIZE:524288000}  # 500MB

geoip:
  db-path: ${GEOIP_DB_PATH:/app/geodata/dbip-city-lite-2025-12.mmdb}

celery:
  broker-url: ${CELERY_BROKER_URL:redis://localhost:6379/0}
  result-backend: ${CELERY_RESULT_BACKEND:redis://localhost:6379/0}
```

## Integration with video_worker

### Option A: Direct Redis/Celery Protocol
- Use a Java Celery client library (if available)
- Send tasks directly to Redis using Celery's protocol
- **Challenge**: Limited Java Celery client libraries

### Option B: HTTP Bridge
- Create a small HTTP service that receives requests from Spring Boot
- HTTP service sends tasks to Celery
- **Pros**: Simple, language-agnostic
- **Cons**: Additional service layer

### Option C: Redis Pub/Sub
- Spring Boot publishes task messages to Redis
- Python service subscribes and processes
- **Pros**: Direct Redis integration
- **Cons**: Need to modify video_worker

### Option D: Keep FastAPI as Task Gateway
- Spring Boot calls FastAPI endpoint for video processing
- FastAPI sends task to Celery
- **Pros**: No changes to video_worker
- **Cons**: Requires FastAPI to be running

**Recommendation**: Option D (simplest) or Option B (cleanest long-term)

## Docker Integration

### Updated `docker-compose.yml`
```yaml
services:
  # ... existing services (postgres, redis, video_worker) ...
  
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
      # ... other env vars ...
    ports:
      - "${SPRING_BACKEND_PORT:-8080}:8080"
    volumes:
      - ./backend-spring:/app
      - backend_uploads:/app/uploads
      - ./geodata:/app/geodata:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - short5_network
```

## Deployment Strategy

### Development
- Run both backends simultaneously
- Use different ports (FastAPI: 8000, Spring Boot: 8080)
- Frontend can be configured to use either backend

### Production
- Choose one backend (FastAPI or Spring Boot)
- Or use both with load balancing (different endpoints)
- Same database, Redis, and video_worker for both

## Next Steps

1. ✅ Create migration analysis (this document)
2. ✅ Create Spring Boot project structure
3. ✅ Set up basic configuration
4. ✅ Implement core entities
5. ✅ Implement authentication
6. ✅ Implement API endpoints incrementally
7. ✅ Test integration with existing services
8. ✅ Update Docker Compose
9. ✅ Update documentation

**Status**: All migration steps have been completed! See [IMPLEMENTATION.md](IMPLEMENTATION.md) for current status.

## Questions & Considerations

1. **Port Configuration**: Should Spring Boot use a different port (8080) or replace FastAPI (8000)?
   - **Recommendation**: Use 8080 for Spring Boot, allow both to run

2. **Database Migrations**: Should Spring Boot use Flyway/Liquibase or rely on existing migrations?
   - **Recommendation**: Use Flyway for Spring Boot, but validate against existing schema

3. **API Compatibility**: Should Spring Boot maintain 100% API compatibility with FastAPI?
   - **Recommendation**: Yes, for seamless frontend switching

4. **Performance**: Any performance requirements?
   - **Note**: Spring Boot with JPA may have different performance characteristics than async FastAPI

5. **Testing Strategy**: How to test both backends?
   - **Recommendation**: Integration tests that work with both backends

