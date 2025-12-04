# Coolify Deployment Guide

This guide explains how to deploy the Short5 Platform on Coolify using the provided `docker-compose.coolify.yaml` configuration.

## Prerequisites

1. A Coolify instance running (self-hosted or cloud)
2. Domain names configured for:
   - Frontend (e.g., `app.yourdomain.com`)
   - Backend API (e.g., `api.yourdomain.com`)
   - Optional: Flower monitoring (e.g., `flower.yourdomain.com`)

## Configuration Overview

The `docker-compose.coolify.yaml` file is configured to work with Coolify's automatic Traefik routing:

- **Frontend**: Exposed via Traefik using `SERVICE_URL_FRONTEND`
- **Backend**: Exposed via Traefik using `SERVICE_URL_BACKEND`
- **Internal Services**: PostgreSQL, Redis, Video Worker (not exposed publicly)
- **Optional**: Flower monitoring (can be exposed or kept internal)

## Required Environment Variables

Set these in Coolify's environment variables section:

### Core Configuration

```bash
# Database
POSTGRES_USER=short5_user
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=short5_db

# Backend Configuration
JWT_SECRET_KEY=<strong-random-secret-key>
ENVIRONMENT=production

# Frontend/Backend URLs (Coolify automatically sets SERVICE_URL_*)
# SERVICE_URL_FRONTEND is automatically set by Coolify based on your service FQDN
# SERVICE_URL_BACKEND is automatically set by Coolify based on your service FQDN

# CORS Origins (include your frontend domain)
CORS_ORIGINS=https://app.yourdomain.com

# Worker Configuration
WORKER_CONCURRENCY=2

# Optional: Flower Monitoring
FLOWER_USER=admin
FLOWER_PASSWORD=<strong-password>
```

### Coolify-Specific Variables

Coolify automatically provides these variables (no need to set manually):

- `SERVICE_URL_FRONTEND` - Full URL for frontend (e.g., `https://app.yourdomain.com`)
- `SERVICE_URL_BACKEND` - Full URL for backend (e.g., `https://api.yourdomain.com`)
- `SERVICE_URL_FLOWER` - Full URL for flower (if exposed)

## Deployment Steps

### 1. Create a New Service in Coolify

1. Go to your Coolify dashboard
2. Navigate to **Services** → **New Service**
3. Select **Docker Compose**
4. Choose your repository and branch

### 2. Configure Docker Compose File

- **Compose File Path**: `docker-compose.coolify.yaml`

### 3. Set Up Service URLs

Coolify will prompt you to set FQDNs for each exposed service:

1. **Frontend Service**:
   - FQDN: `app.yourdomain.com` (or your chosen domain)
   - This sets `SERVICE_URL_FRONTEND`

2. **Backend Service**:
   - FQDN: `api.yourdomain.com` (or your chosen domain)
   - This sets `SERVICE_URL_BACKEND`

3. **Optional - Flower Service**:
   - If you want to expose Flower, uncomment the Traefik labels in `docker-compose.coolify.yaml`
   - FQDN: `flower.yourdomain.com`
   - This sets `SERVICE_URL_FLOWER`

### 4. Configure Environment Variables

Add all required environment variables in Coolify's environment variables section (see above).

**Important**: 
- `BACKEND_BASE_URL` is automatically set from `SERVICE_URL_BACKEND` in the compose file
- Frontend API URLs are automatically derived from `SERVICE_URL_BACKEND`

### 5. Deploy

1. Review all configurations
2. Click **Deploy**
3. Coolify will:
   - Build all Docker images
   - Start services in the correct order (health checks ensure dependencies)
   - Set up Traefik routing automatically
   - Provision SSL certificates via Let's Encrypt

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Coolify Network                       │
│                  (Traefik + SSL)                         │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
┌───────▼────────┐                  ┌───────▼────────┐
│   Frontend     │                  │    Backend     │
│  (Nuxt 4)      │ ────────────────▶│  (FastAPI)     │
│ Port: 3000     │   API Calls      │ Port: 8000     │
└────────────────┘                  └───────┬────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
            ┌───────▼────────┐     ┌───────▼────────┐     ┌───────▼────────┐
            │  PostgreSQL    │     │     Redis      │     │ Video Worker   │
            │  (Internal)    │     │   (Internal)   │     │   (Internal)   │
            └────────────────┘     └────────────────┘     └────────────────┘
```

## Service Details

### Exposed Services (via Traefik)

- **Frontend**: Publicly accessible web application
- **Backend**: Public API endpoint with automatic SSL

### Internal Services (not exposed)

- **PostgreSQL**: Database (accessible only within Docker network)
- **Redis**: Message broker (accessible only within Docker network)
- **Video Worker**: Celery worker for video processing
- **Flower**: Monitoring dashboard (can be exposed or kept internal)

## Health Checks

All services include health checks:

- **Backend**: Checks `/health` endpoint
- **PostgreSQL**: `pg_isready` check
- **Redis**: `redis-cli ping` check
- **Video Worker**: Celery ping check
- **Frontend**: HTTP health check

Services will only start once their dependencies are healthy.

## SSL Certificates

Traefik automatically provisions SSL certificates via Let's Encrypt for all exposed services. No manual configuration needed.

## Monitoring

### Flower (Celery Monitoring)

Flower is included but not exposed by default. To expose it:

1. Uncomment the Traefik labels in the `flower` service section
2. Uncomment the `coolify` network for flower service
3. Set up FQDN in Coolify for the flower service
4. Access at `https://flower.yourdomain.com` (with HTTP basic auth)

### Logs

View logs in Coolify dashboard:
- Service-specific logs
- Container logs
- Traefik access logs

## Troubleshooting

### Services Won't Start

1. Check environment variables are set correctly
2. Verify database credentials
3. Check Coolify logs for startup errors
4. Ensure all required secrets are set (JWT_SECRET_KEY, POSTGRES_PASSWORD, etc.)

### Frontend Can't Reach Backend

1. Verify `SERVICE_URL_BACKEND` is set correctly
2. Check CORS configuration includes frontend URL
3. Verify backend is healthy (check `/health` endpoint)

### Video Processing Not Working

1. Check video_worker logs in Coolify
2. Verify Redis connection
3. Check database connectivity from worker
4. Verify shared volume mount for uploads

### Database Connection Issues

1. Verify PostgreSQL service is running
2. Check `POSTGRES_USER` and `POSTGRES_PASSWORD` match
3. Verify network connectivity (services use Docker service names)

## Updates and Rollbacks

1. **Update**: Push changes to your repository, Coolify will detect and rebuild
2. **Rollback**: Use Coolify's rollback feature if needed
3. **Database Migrations**: Run manually via `docker-compose exec` or include in startup

## Production Checklist

- [ ] All environment variables set
- [ ] Strong passwords for database and JWT
- [ ] CORS origins configured correctly
- [ ] SSL certificates provisioned (automatic)
- [ ] Health checks passing
- [ ] Video worker processing tasks
- [ ] Database initialized with schema
- [ ] Monitoring configured (optional)

## Notes

- Coolify handles port mapping automatically via Traefik
- Service-to-service communication uses Docker service names (e.g., `postgres`, `redis`)
- Public URLs are handled by Traefik with automatic SSL
- Volume data persists across deployments
- Environment variables can be updated without redeploying (for some variables)

## Support

For issues specific to:
- **Coolify**: Check [Coolify documentation](https://coolify.io/docs)
- **Application**: Check application logs and health endpoints
