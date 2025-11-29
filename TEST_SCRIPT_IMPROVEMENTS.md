# Test Script Improvements

## Overview

Updated both `test-browser.ps1` and `test-browser.sh` to **ALWAYS restart Docker containers** when testing, ensuring that code changes are properly loaded in the Docker development environment.

## Key Changes

### 1. **Mandatory Container Restart**
- Scripts now **always** stop and restart containers before testing
- This ensures latest code changes are loaded (required for Docker development)
- Clear messaging that containers will be restarted

### 2. **Enhanced Error Handling**
- Better error checking for `docker compose down` and `docker compose up`
- Verification that containers actually started successfully
- Container count validation (expects 6 containers: frontend, backend, postgres, redis, celery_worker, video_worker)

### 3. **Rebuild Option**
- Added `--rebuild` flag to rebuild Docker images when dependencies change
- Usage: `.\test-browser.ps1 --rebuild` or `./test-browser.sh --rebuild`
- Useful when `package.json`, `requirements.txt`, or Dockerfiles change

### 4. **Improved Messaging**
- Clear warnings that containers will be restarted
- Step-by-step progress indicators
- Reminders to run script again after code changes
- Helpful tips about when to use `--rebuild` flag

### 5. **Better Verification**
- Checks that all expected containers are running
- Validates services are ready before testing
- TypeScript checking before proceeding
- API endpoint validation

## Why This Matters

**In Docker development environments:**
- Code changes in mounted volumes may not always hot-reload properly
- Some changes (TypeScript types, dependencies, config) require full restarts
- Container restarts ensure a clean state with latest code
- Prevents issues from stale code or cached builds

## Usage

### Normal Testing (After Code Changes)
```powershell
# PowerShell
.\test-browser.ps1
```

```bash
# Bash
./test-browser.sh
```

### After Dependency Changes
```powershell
# PowerShell
.\test-browser.ps1 --rebuild
```

```bash
# Bash
./test-browser.sh --rebuild
```

## Script Flow

1. **Stop Containers** - Ensures clean state
2. **Rebuild Images** (optional) - If `--rebuild` flag used
3. **Start Containers** - Loads latest code
4. **Verify Containers** - Checks all are running
5. **Wait for Services** - Backend and frontend ready
6. **TypeScript Check** - Validates code is type-safe
7. **API Tests** - Verifies endpoints work
8. **Success Message** - Ready for browser testing

## What Gets Restarted

- ✅ `short5_frontend` - Nuxt frontend
- ✅ `short5_backend` - FastAPI backend  
- ✅ `short5_postgres` - PostgreSQL database
- ✅ `short5_redis` - Redis cache/broker
- ✅ `short5_celery_worker` - Celery worker
- ✅ `short5_video_worker` - Video processing worker

## Important Notes

⚠️ **Always run this script after making code changes** to ensure containers restart with the latest code.

💡 **Use `--rebuild` flag** when you:
- Change `package.json` or `package-lock.json`
- Change `requirements.txt` or `Pipfile`
- Modify Dockerfiles
- Add new dependencies

✅ **Normal code changes** (TypeScript, Python, Vue components) just need the regular script run (containers restart automatically).
