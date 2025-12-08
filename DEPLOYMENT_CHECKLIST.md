# Visitor Analytics - Deployment Checklist

## ✅ Implementation Complete

All code has been implemented and is ready for deployment.

## Pre-Deployment Steps

### 1. Database Migration
Run the migration to create the `visitor_logs` table:

```bash
# Using psql
psql -U short5_user -d short5_db -f database/migrations/002_visitor_analytics.sql

# Or using docker exec
docker exec -i short5_postgres psql -U short5_user -d short5_db < database/migrations/002_visitor_analytics.sql
```

### 2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
# Or if using Docker, rebuild the container
docker-compose build backend
```

### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
# This will install Leaflet for the map component
```

### 4. GeoIP Database (Optional but Recommended)
The system works without GeoIP, but geographic data won't be available.

**To enable geographic tracking:**
1. Register for free MaxMind account: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
2. Download `GeoLite2-City.mmdb` file
3. Place it in `backend/data/GeoLite2-City.mmdb`
4. Or set environment variable: `GEOIP_DB_PATH=/path/to/GeoLite2-City.mmdb`

**Docker Setup:**
- Option 1: Mount as volume in `docker-compose.yml`:
  ```yaml
  backend:
    volumes:
      - ./backend/data/GeoLite2-City.mmdb:/app/data/GeoLite2-City.mmdb:ro
  ```
- Option 2: Copy into Docker image in `backend/Dockerfile`:
  ```dockerfile
  COPY data/GeoLite2-City.mmdb /app/data/GeoLite2-City.mmdb
  ```

### 5. Restart Services
```bash
docker-compose restart backend frontend
# Or if running locally:
# Restart backend and frontend servers
```

## Testing

### 1. Verify Database Table
```sql
-- Check if table exists
SELECT * FROM visitor_logs LIMIT 1;
```

### 2. Test API Endpoints (as admin)
```bash
# Get visitor stats
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/visitors/stats?days=30

# Get visitor locations
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/visitors/locations?days=7

# Get recent visits
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/visitors/recent?limit=10
```

### 3. Test Frontend
1. Log in as admin
2. Navigate to `/admin`
3. Click on "Visitor Analytics" tab
4. Verify:
   - Summary cards show data
   - Map displays (if locations exist)
   - Top countries/cities/URLs lists work
   - Recent visits table displays

### 4. Test Tracking
1. Visit the frontend from different browsers/locations
2. Check that visits are being tracked:
   ```sql
   SELECT COUNT(*) FROM visitor_logs;
   SELECT * FROM visitor_logs ORDER BY visited_at DESC LIMIT 10;
   ```

## Expected Behavior

### Without GeoIP Database
- ✅ Tracking works (visits are logged)
- ✅ URLs are tracked
- ✅ Session IDs are tracked
- ❌ Geographic data (country, city, coordinates) will be NULL

### With GeoIP Database
- ✅ All features work
- ✅ Geographic data is populated
- ✅ Map visualization shows visitor locations

## Troubleshooting

### No visits being tracked
- Check middleware is running (check logs)
- Verify database connection
- Check that routes are not starting with `/api/` (only frontend routes are tracked)

### Map not displaying
- Check browser console for errors
- Verify Leaflet is installed: `npm list leaflet`
- Check that locations data is being returned from API

### GeoIP not working
- Verify database file exists and is readable
- Check logs for GeoIP errors
- Verify `GEOIP_DB_PATH` is set correctly (if using env var)

## Files Created/Modified

### Backend
- ✅ `database/migrations/002_visitor_analytics.sql` - Database migration
- ✅ `backend/app/models/visitor_log.py` - Visitor log model
- ✅ `backend/app/services/geoip_service.py` - GeoIP service
- ✅ `backend/app/services/visitor_tracking.py` - Tracking service
- ✅ `backend/app/api/v1/visitor_analytics.py` - API endpoints
- ✅ `backend/app/core/config.py` - Added GEOIP_DB_PATH
- ✅ `backend/app/main.py` - Added tracking middleware
- ✅ `backend/requirements.txt` - Added geoip2, maxminddb

### Frontend
- ✅ `frontend/components/VisitorMap.vue` - Map component
- ✅ `frontend/pages/admin.vue` - Added Visitor Analytics tab
- ✅ `frontend/package.json` - Added leaflet

## Notes

- Tracking is non-blocking (runs in background)
- Only GET requests to frontend routes are tracked (API routes are skipped)
- The module is designed to be modular and reusable
- All geographic data is optional - system works without GeoIP database

