# Database Container Troubleshooting Guide

## Quick Start

1. **Make sure Docker Desktop is running**
   - Check the system tray for Docker icon
   - If not running, start Docker Desktop

2. **Start the database container:**
   ```powershell
   cd C:\Users\nadob\Desktop\short5_swiper_bugagaa
   docker compose up -d postgres
   ```

3. **Check if it's running:**
   ```powershell
   docker compose ps postgres
   ```

4. **View logs if there are errors:**
   ```powershell
   docker compose logs postgres
   ```

## Common Issues and Solutions

### Issue 1: Port 5432 already in use

**Error:** `port is already allocated` or `bind: address already in use`

**Solution:**
- Check if another PostgreSQL instance is running:
  ```powershell
  netstat -ano | findstr :5432
  ```
- Stop the conflicting service or change the port in `.env`:
  ```
  POSTGRES_PORT=5433
  ```
- Update `DATABASE_URL` in `.env` to match:
  ```
  DATABASE_URL=postgresql://short5_user:short5_password@localhost:5433/short5_db
  ```

### Issue 2: Container starts but immediately exits

**Check logs:**
```powershell
docker compose logs postgres
```

**Common causes:**
- Corrupted volume data
- Permission issues with schema.sql file

**Solution - Reset the database:**
```powershell
# Stop and remove container and volume
docker compose down postgres
docker volume rm short5_swiper_bugagaa_postgres_data

# Start fresh
docker compose up -d postgres
```

### Issue 3: Schema file not found

**Error:** `no such file or directory: ./database/schema.sql`

**Solution:**
- Verify the file exists:
  ```powershell
  Test-Path .\database\schema.sql
  ```
- If missing, check the `database` folder structure

### Issue 4: Permission denied errors

**Solution:**
- On Windows, make sure Docker Desktop has proper file sharing permissions
- Check Docker Desktop Settings > Resources > File Sharing
- Ensure the project directory is shared

### Issue 5: Network issues

**Error:** `network short5_network not found`

**Solution:**
```powershell
# Create the network manually
docker network create short5_network

# Or restart all services
docker compose down
docker compose up -d
```

## Manual Database Setup (Alternative)

If Docker continues to have issues, you can set up PostgreSQL manually:

1. **Install PostgreSQL locally** (if not already installed)
2. **Create database and user:**
   ```sql
   CREATE USER short5_user WITH PASSWORD 'short5_password';
   CREATE DATABASE short5_db OWNER short5_user;
   ```
3. **Run the schema:**
   ```powershell
   psql -U short5_user -d short5_db -f database\schema.sql
   ```

## Verify Database Connection

Test the connection:
```powershell
# Using docker exec (if container is running)
docker exec -it short5_postgres psql -U short5_user -d short5_db

# Or using local psql
psql -U short5_user -d short5_db -h localhost
```

## Check Current Status

```powershell
# List all containers
docker ps -a

# Check postgres specifically
docker compose ps postgres

# View real-time logs
docker compose logs -f postgres

# Check container health
docker inspect short5_postgres | Select-String -Pattern "Health"
```
