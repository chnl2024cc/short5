# Starting and Testing the Spring Boot Backend

This guide provides step-by-step instructions for starting and testing the Spring Boot backend.

## Prerequisites

Before starting, ensure you have:

- **Java 17+** (check with `java -version`)
- **Maven 3.6+** (check with `mvn -version`)
- **PostgreSQL 15+** running and accessible
- **Redis 7+** running and accessible
- **Environment variables** configured (see below)

## Quick Start Options

### Option 1: Local Development (Recommended for Testing)

#### Step 1: Configure Environment Variables

Set the following environment variables (or create a `.env` file):

```bash
# Database
export DATABASE_URL="jdbc:postgresql://localhost:5432/short5_db"
export POSTGRES_USER="short5_user"
export POSTGRES_PASSWORD="short5_password"

# Redis
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# JWT
export JWT_SECRET_KEY="your-secret-key-change-in-production"

# File Uploads
export UPLOAD_DIR="./uploads"  # Local directory for development

# Server Port
export SPRING_BACKEND_PORT="8080"
```

**Windows PowerShell:**
```powershell
$env:DATABASE_URL="jdbc:postgresql://localhost:5432/short5_db"
$env:POSTGRES_USER="short5_user"
$env:POSTGRES_PASSWORD="short5_password"
$env:REDIS_HOST="localhost"
$env:REDIS_PORT="6379"
$env:JWT_SECRET_KEY="your-secret-key-change-in-production"
$env:UPLOAD_DIR="./uploads"
$env:SPRING_BACKEND_PORT="8080"
```

#### Step 2: Navigate to Backend Directory

```bash
cd backend-spring
```

#### Step 3: Build the Project

```bash
mvn clean package
```

#### Step 4: Run the Application

**Option A: Using Maven Spring Boot Plugin (Recommended for Development)**
```bash
mvn spring-boot:run
```

**Option B: Using the JAR file**
```bash
java -jar target/short5-backend-spring-1.0.0.jar
```

#### Step 5: Verify the Application Started

The application should start on port 8080 (or your configured port). Check:

1. **Health Endpoint:**
   ```bash
   curl http://localhost:8080/actuator/health
   ```
   Expected response: `{"status":"UP"}`

2. **Root Endpoint:**
   ```bash
   curl http://localhost:8080/
   ```
   Expected response: API information JSON

3. **Check Logs:**
   Look for: `Started Short5Application in X.XXX seconds`

---

### Option 2: Docker Compose (Recommended for Production-like Testing)

#### Step 1: Check Docker Compose Configuration

Ensure your `docker-compose.yml` includes the Spring backend service (see `QUICK_START.md` for configuration).

#### Step 2: Start Services

```bash
# Start all services including Spring backend
docker-compose up -d backend-spring

# Or start all services
docker-compose up -d
```

#### Step 3: Check Logs

```bash
docker-compose logs -f backend-spring
```

#### Step 4: Verify Health

```bash
curl http://localhost:8080/actuator/health
```

---

## Testing the Backend

### 1. Run Unit Tests

```bash
cd backend-spring
mvn test
```

This will run all unit tests including:
- Service tests (AuthService, UserService, VideoService, etc.)
- Controller tests (AuthController, VideoController, etc.)
- Repository tests
- Security tests (JWT)

### 2. Test Specific Components

**Run a specific test class:**
```bash
mvn test -Dtest=AuthServiceTest
```

**Run tests with coverage:**
```bash
mvn test jacoco:report
```

### 3. Manual API Testing

#### Test Authentication Endpoints

**Register a new user:**
```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPassword123!"
  }'
```

Save the `access_token` from the response for authenticated requests.

#### Test Video Endpoints

**Get feed (public endpoint):**
```bash
curl http://localhost:8080/api/v1/feed
```

**Get a specific video (public endpoint):**
```bash
curl http://localhost:8080/api/v1/videos/{video-id}
```

**Upload a video (requires authentication):**
```bash
curl -X POST http://localhost:8080/api/v1/videos/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/video.mp4" \
  -F "title=My Video" \
  -F "description=Video description"
```

#### Test Admin Endpoints

**Get reports (requires admin role):**
```bash
curl http://localhost:8080/api/v1/admin/reports \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**Test Bug Fix 1: Invalid status parameter**
```bash
# This should return 400 Bad Request (not 500)
curl "http://localhost:8080/api/v1/admin/reports?status=INVALID_STATUS" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**Get reports with valid status:**
```bash
# Valid statuses: PENDING, RESOLVED, DISMISSED
curl "http://localhost:8080/api/v1/admin/reports?status=PENDING" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### Test Security Configuration (Bug Fix 3)

**Test video endpoint access (should work without auth):**
```bash
curl http://localhost:8080/api/v1/videos/{video-id}
```

This should work because `/api/v1/videos/*` is now properly configured as a public endpoint.

### 4. Integration Testing with Postman/Insomnia

1. **Import API Collection:**
   - See `docs/API.md` for complete endpoint documentation
   - Create a Postman collection with all endpoints

2. **Set Environment Variables:**
   - `base_url`: `http://localhost:8080`
   - `access_token`: (set after login)

3. **Test Workflow:**
   - Register → Login → Get User Profile → Upload Video → Get Feed

### 5. Test the Fixed Bugs

#### Bug 1: Invalid Enum Status Handling

**Before fix:** Would return 500 Internal Server Error  
**After fix:** Should return 400 Bad Request

```bash
# Test invalid status
curl -v "http://localhost:8080/api/v1/admin/reports?status=INVALID" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Should return: HTTP/1.1 400 Bad Request
```

#### Bug 2: Duplicate Resource Handler

**Verification:**
- Check application logs for any warnings about duplicate resource handlers
- Verify `/uploads/**` files are accessible:
  ```bash
  curl http://localhost:8080/uploads/processed/{videoId}/video.mp4
  ```

#### Bug 3: Video Endpoint Security Pattern

**Test:**
```bash
# Should work without authentication (public endpoint)
curl http://localhost:8080/api/v1/videos/550e8400-e29b-41d4-a716-446655440000

# Should return video data or 404 (not 401 Unauthorized)
```

---

## Troubleshooting

### Application Won't Start

**Issue: Database Connection Failed**
```
Error: Connection to localhost:5432 refused
```
**Solution:**
- Ensure PostgreSQL is running: `pg_isready` or check service status
- Verify database credentials in environment variables
- Check if database `short5_db` exists

**Issue: Redis Connection Failed**
```
Error: Unable to connect to Redis
```
**Solution:**
- Ensure Redis is running: `redis-cli ping` (should return `PONG`)
- Verify Redis host and port in environment variables

**Issue: Port Already in Use**
```
Error: Port 8080 is already in use
```
**Solution:**
- Change port: `export SPRING_BACKEND_PORT="8081"`
- Or stop the service using port 8080

### Tests Failing

**Issue: Database Connection in Tests**
- Tests use H2 in-memory database, no PostgreSQL needed
- Check `application-test.yml` configuration

**Issue: Security Tests Failing**
- Ensure `@WithMockUser` annotations are used
- Check security auto-configuration exclusions

### API Requests Failing

**Issue: 401 Unauthorized**
- Ensure JWT token is included: `Authorization: Bearer <token>`
- Check token hasn't expired
- Verify user has required role (e.g., `ROLE_ADMIN` for admin endpoints)

**Issue: 400 Bad Request**
- Check request body format (JSON)
- Verify required fields are present
- Check enum values are valid (e.g., report status)

**Issue: 500 Internal Server Error**
- Check application logs for stack traces
- Verify database schema matches entities
- Check file upload directory permissions

---

## Development Workflow

### 1. Start Development Server

```bash
# Terminal 1: Start Spring Boot with hot reload (if using Spring Boot DevTools)
mvn spring-boot:run

# Or use IDE run configuration
```

### 2. Run Tests Continuously

```bash
# Terminal 2: Watch for changes and run tests
mvn test

# Or use IDE test runner
```

### 3. Monitor Logs

```bash
# Check application logs
tail -f logs/application.log

# Or view in IDE console
```

### 4. Make Changes and Test

1. Make code changes
2. Application auto-reloads (if DevTools enabled)
3. Run tests: `mvn test`
4. Test API endpoints manually or with Postman

---

## Next Steps

After successfully starting and testing:

1. **Review API Documentation:** See `docs/API.md`
2. **Check Implementation Status:** See `docs/IMPLEMENTATION.md`
3. **Read Development Guide:** See `docs/DEVELOPMENT.md`
4. **Set up Frontend Integration:** Configure frontend to use Spring backend

---

## Quick Reference Commands

```bash
# Build
mvn clean package

# Run
mvn spring-boot:run

# Test
mvn test

# Test specific class
mvn test -Dtest=AuthServiceTest

# Check health
curl http://localhost:8080/actuator/health

# View logs (Docker)
docker-compose logs -f backend-spring

# Stop (Docker)
docker-compose stop backend-spring
```

---

**Last Updated:** 2024  
**Spring Boot Version:** 3.2.0  
**Java Version:** 17+

