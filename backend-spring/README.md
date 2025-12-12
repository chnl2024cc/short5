# Short5 Platform - Spring Boot Backend

This is the Spring Boot implementation of the Short5 Platform backend, providing an alternative to the FastAPI backend.

## Features

- ✅ Same API endpoints as FastAPI backend
- ✅ Uses the same PostgreSQL database
- ✅ Integrates with existing Redis and video_worker services
- ✅ JWT authentication
- ✅ File upload and static file serving
- ✅ RESTful API with Spring Data JPA

## Architecture

### Services Integration

- **PostgreSQL**: Same database as FastAPI backend
- **Redis**: Used for caching and task queue
- **video_worker**: Integrated via Celery task protocol (or HTTP bridge)

### Project Structure

```
backend-spring/
├── src/
│   ├── main/
│   │   ├── java/com/short5/
│   │   │   ├── config/          # Configuration classes
│   │   │   ├── controller/     # REST controllers
│   │   │   ├── service/         # Business logic
│   │   │   ├── repository/      # Data access layer
│   │   │   ├── entity/          # JPA entities
│   │   │   ├── dto/             # Data transfer objects
│   │   │   ├── security/        # JWT and security
│   │   │   └── exception/       # Exception handlers
│   │   └── resources/
│   │       └── application.yml # Configuration
│   └── test/                    # Tests
├── pom.xml                      # Maven dependencies
└── Dockerfile                   # Docker build
```

## Configuration

Configuration is done via environment variables (same as FastAPI backend):

- `DATABASE_URL` - PostgreSQL connection string
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `REDIS_HOST` - Redis host
- `REDIS_PORT` - Redis port
- `JWT_SECRET_KEY` - JWT secret key
- `UPLOAD_DIR` - File upload directory (default: `/app/uploads`)
- `SPRING_BACKEND_PORT` - Server port (default: `8080`)

See `src/main/resources/application.yml` for all configuration options.

## Building

### With Maven

```bash
cd backend-spring
mvn clean package
java -jar target/short5-backend-spring-1.0.0.jar
```

### With Docker

```bash
docker build -t short5-backend-spring .
docker run -p 8080:8080 \
  -e DATABASE_URL=jdbc:postgresql://postgres:5432/short5_db \
  -e POSTGRES_USER=short5_user \
  -e POSTGRES_PASSWORD=short5_password \
  -e REDIS_HOST=redis \
  -e JWT_SECRET_KEY=your-secret-key \
  short5-backend-spring
```

## Running with Docker Compose

Add to your `docker-compose.yml`:

```yaml
services:
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
    ports:
      - "${SPRING_BACKEND_PORT:-8080}:8080"
    volumes:
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

## API Endpoints

All endpoints match the FastAPI backend. For complete API documentation, see [docs/API.md](docs/API.md).

Quick reference:
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/videos/{id}` - Get video
- `POST /api/v1/videos/upload` - Upload video
- `GET /api/v1/feed` - Get feed

## Health Check

- Health endpoint: `GET /actuator/health`
- Root endpoint: `GET /` - Returns API info

## Development

### Prerequisites

- Java 17+
- Maven 3.6+
- PostgreSQL 15+
- Redis 7+

### Running Locally

1. Set environment variables (or use `.env` file)
2. Ensure PostgreSQL and Redis are running
3. Run: `mvn spring-boot:run`

### Testing

```bash
mvn test
```

## Integration with video_worker

The Spring Boot backend integrates with the existing Python video_worker via HTTP bridge:

1. **HTTP Bridge** (Implemented): Spring Boot calls FastAPI endpoint which sends tasks to Celery
2. Video processing is triggered asynchronously after upload
3. Processing completion callbacks update video status

For detailed implementation information, see [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md).

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[docs/QUICK_START.md](docs/QUICK_START.md)** - Quick start guide for getting the Spring Boot backend running
- **[docs/MIGRATION.md](docs/MIGRATION.md)** - Migration plan and analysis from FastAPI to Spring Boot
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development guide, best practices, and coding standards
- **[docs/API.md](docs/API.md)** - Complete API endpoints documentation
- **[docs/TESTING.md](docs/TESTING.md)** - Testing guide and test structure
- **[docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)** - Implementation history and status

## Status

✅ **Production Ready**

All core features have been implemented:
- ✅ Complete entity models
- ✅ All API endpoints implemented
- ✅ JWT authentication service
- ✅ File upload service
- ✅ Feed/recommendation algorithm
- ✅ Integration with video_worker
- ✅ Unit and integration tests

## License

Same as main project.

