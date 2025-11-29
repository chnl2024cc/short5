# Log Filtering Guide

## Filtering `[VIDEO_TASK]` Logs

The backend uses special `[VIDEO_TASK]` prefixed logs for video processing task debugging. Here's how to filter them.

## Option 1: Filter from Host (Recommended)

Since Docker logs go to stdout/stderr, filter them from outside the container:

### PowerShell (Windows)
```powershell
# Real-time monitoring
docker-compose logs -f backend | Select-String "\[VIDEO_TASK\]"

# View recent logs
docker-compose logs backend | Select-String "\[VIDEO_TASK\]"

# Last 100 lines with context
docker-compose logs --tail=100 backend | Select-String "\[VIDEO_TASK\]" -Context 2,2

# Save filtered logs to file
docker-compose logs backend | Select-String "\[VIDEO_TASK\]" | Out-File video_task_logs.txt
```

### Bash/Linux/WSL
```bash
# Real-time monitoring
docker-compose logs -f backend | grep "\[VIDEO_TASK\]"

# View recent logs
docker-compose logs backend | grep "\[VIDEO_TASK\]"

# With context (2 lines before/after)
docker-compose logs backend | grep -A 2 -B 2 "\[VIDEO_TASK\]"
```

## Option 2: Use grep Inside Container

If you need to run commands inside the container:

```powershell
# Enter the backend container
docker-compose exec backend bash

# Check if grep is available
grep --version

# If logs are written to files (check your logging config)
grep "\[VIDEO_TASK\]" /path/to/logfile
```

**Note:** Since logs typically go to stdout/stderr, filtering from outside is usually better.

## Quick Reference

### Container Names
- Backend: `short5_backend` or use service name `backend`
- Video Worker: `short5_video_worker` or use service name `video_worker`

### Common Commands

```powershell
# Backend logs (all)
docker-compose logs -f backend

# Backend logs (filtered)
docker-compose logs -f backend | Select-String "\[VIDEO_TASK\]"

# Video worker logs
docker-compose logs -f video_worker

# Multiple services
docker-compose logs -f backend video_worker | Select-String "\[VIDEO_TASK\]"
```

## PowerShell Alias (Optional)

Add to your PowerShell profile for quick access:

```powershell
function Get-VideoTaskLogs {
    docker-compose logs -f backend | Select-String "\[VIDEO_TASK\]"
}

# Usage
Get-VideoTaskLogs
```

## What `[VIDEO_TASK]` Logs Include

- Pre-task state: file path, size, existence, Celery app type
- Task queuing: task ID, queue name, result state
- Errors: error type, context, file existence status

These logs help debug video processing task issues without flooding the main logs.
