# GeoIP Database Setup

## Supported Databases

The visitor analytics system supports **both** MaxMind GeoLite2 and DB-IP databases:

- **MaxMind GeoLite2-City.mmdb** - Free database from MaxMind
- **DB-IP dbip-city-lite-*.mmdb** - Free database from DB-IP

Both use the same `.mmdb` format and are compatible with the `geoip2` Python library.

## Current Setup

You have a **DB-IP database** file located at:
```
geodata/dbip-city-lite-2025-12.mmdb
```

The system will automatically detect and use this file!

## How It Works

1. **Auto-Detection**: The system automatically searches for database files in these locations (in order):
   - `geodata/dbip-city-lite-2025-12.mmdb` (your current file)
   - `data/GeoLite2-City.mmdb` (MaxMind alternative)
   - Docker paths: `/app/geodata/` or `/app/data/`

2. **Manual Path**: You can also set the path explicitly via environment variable:
   ```bash
   GEOIP_DB_PATH=C:\Users\nadob\Desktop\short5_swiper_bugagaa\geodata\dbip-city-lite-2025-12.mmdb
   ```

3. **Lazy Loading**: The database is only loaded when a visitor lookup is actually performed (not on startup).

## Docker Setup

If using Docker, you need to mount the `geodata` folder:

```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - ./geodata:/app/geodata:ro  # Read-only mount
```

Or copy it into the Docker image:

```dockerfile
# backend/Dockerfile
COPY geodata/ /app/geodata/
```

## Features Available

With your DB-IP database, you'll get:
- ✅ Country detection (ISO code and name)
- ✅ City detection
- ✅ Latitude/Longitude coordinates
- ✅ Map visualization in admin dashboard
- ✅ Top countries/cities statistics

## Database Updates

DB-IP databases are updated monthly. To update:
1. Download the latest `dbip-city-lite-YYYY-MM.mmdb` file
2. Replace the file in `geodata/` folder
3. Restart the backend service

## Testing

To verify the database is working:
1. Visit your site from different locations
2. Check the admin dashboard → Visitor Analytics
3. You should see countries, cities, and map markers

## Troubleshooting

**Database not loading?**
- Check file path is correct
- Verify file permissions (readable)
- Check backend logs for GeoIP messages

**No geographic data?**
- Verify database file exists and is readable
- Check that IP addresses are being tracked
- Some IPs may not have geographic data in the database

