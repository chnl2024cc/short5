# Testing Guide

## Quick Test Commands

### Manual Testing
```bash
# Restart everything
docker compose down && docker compose up -d

# Wait for services (or use the script)
# Then open browser to http://localhost:3000
```

### Automated Testing Scripts

#### Windows (PowerShell)
```powershell
.\test-browser.ps1
```

#### Linux/Mac/Git Bash
```bash
chmod +x test-browser.sh
./test-browser.sh
```

## What Gets Tested

1. **Docker Services**
   - Containers start successfully
   - All services are healthy

2. **Backend API**
   - Health endpoint (`/health`)
   - Feed endpoint (`/api/v1/feed`)

3. **Frontend**
   - Page loads correctly
   - Navigation works
   - No console errors
   - Components render

4. **Integration**
   - Frontend can communicate with backend
   - API calls succeed
   - CORS is configured correctly

## Expected Results

✅ **Success Indicators:**
- All Docker containers running
- Backend health check returns "healthy"
- Frontend loads without errors
- API endpoints respond correctly
- No JavaScript runtime errors

⚠️ **Known Non-Critical Issues:**
- TypeScript overlay may show phantom errors (Nuxt dev tools caching)
- These don't affect functionality

## Browser Testing Checklist

When testing manually in browser:

- [ ] Homepage loads (`http://localhost:3000`)
- [ ] Shows "No videos available" or video feed
- [ ] Login link works
- [ ] Login page loads with form
- [ ] No console errors (F12 → Console)
- [ ] Network tab shows successful API calls
- [ ] Navigation between pages works smoothly

## Troubleshooting

### Services won't start
```bash
# Check logs
docker compose logs

# Check specific service
docker compose logs backend
docker compose logs frontend
```

### Frontend not loading
- Check if port 3000 is available
- Verify frontend container is running: `docker ps`
- Check frontend logs: `docker compose logs frontend`

### Backend not responding
- Check if port 8000 is available
- Verify backend container is running: `docker ps`
- Check backend logs: `docker compose logs backend`
- Test health endpoint: `curl http://localhost:8000/health`

### TypeScript errors in browser
- These are usually cached by Nuxt dev tools
- Restart dev server: Stop and restart `docker compose up -d`
- Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
