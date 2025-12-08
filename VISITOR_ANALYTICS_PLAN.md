# Visitor Analytics Dashboard - Implementation Plan (MVP)

## Overview
Create a minimal, reusable analytics module where admins can see visitor information including:
- Geographic data: Country, City, Coordinates
- URL tracking: Which URLs visitors are accessing
- Map visualization: Interactive map showing visitor locations

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (async)
- **GeoIP**: MaxMind GeoLite2 (local database file, free, no external API calls)
- **Architecture**: Modular design with separate service layer for reusability

### Frontend
- **Framework**: Nuxt 4 / Vue 3
- **Map Library**: Leaflet (open-source, no API key required)
- **HTTP Client**: Native fetch or existing API composable
- **State Management**: Pinia (existing)

### Deployment Architecture
- **MVP Approach**: Integrated into main backend container (simpler, shared database)
- **Alternative**: Can be extracted to separate container if needed (more modular)
- **Current Setup**: Single `backend` container running FastAPI app

### Design Principles
- **Modular**: Separate analytics module that can be extracted/reused
- **Self-contained**: No external API dependencies
- **Minimal**: MVP focus - core features only
- **Loosely Coupled**: Can be easily integrated or removed

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Frontend (Nuxt/Vue)             │
│  - Admin Dashboard Tab                   │
│  - VisitorMap Component (Leaflet)      │
│  - Analytics Tables                     │
└──────────────┬──────────────────────────┘
               │
               │ HTTP REST API
               │
┌──────────────▼──────────────────────────┐
│      Backend (FastAPI)                  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Analytics Module (Reusable)     │  │
│  │  - visitor_tracking.py           │  │
│  │  - geoip_service.py               │  │
│  │  - visitor_analytics.py (API)    │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Local GeoIP Database            │  │
│  │  (MaxMind GeoLite2 .mmdb file)   │  │
│  └──────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │
               │
┌──────────────▼──────────────────────────┐
│      Database (PostgreSQL)              │
│  - visitor_logs table                   │
└─────────────────────────────────────────┘
```

---

## Phase 1: Database Schema (MVP)

### 1.1 Create `visitor_logs` Table

**Location**: `database/migrations/002_visitor_analytics.sql`

**MVP Scope**: Minimal schema with essential fields only.

```sql
-- Visitor Logs Table (MVP - Minimal Implementation)
CREATE TABLE visitor_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Session/User Identification
    session_id UUID NOT NULL, -- Anonymous session or user session
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- NULL for anonymous users
    
    -- Request Information (Core)
    url TEXT NOT NULL, -- The URL/page visited
    ip_address INET, -- IP address (used for GeoIP lookup)
    user_agent TEXT, -- User agent string
    
    -- Geographic Information (Core)
    country VARCHAR(2), -- ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB')
    country_name VARCHAR(100), -- Full country name
    city VARCHAR(100), -- City name
    latitude DECIMAL(10, 8), -- Latitude coordinate
    longitude DECIMAL(11, 8), -- Longitude coordinate
    
    -- Timestamps
    visited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Essential indexes only (MVP)
CREATE INDEX idx_visitor_logs_visited_at ON visitor_logs(visited_at DESC);
CREATE INDEX idx_visitor_logs_url ON visitor_logs(url);
CREATE INDEX idx_visitor_logs_country ON visitor_logs(country);
CREATE INDEX idx_visitor_logs_coordinates ON visitor_logs(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
```

**Note**: Additional fields (device_type, browser, os, timezone, metadata) can be added later if needed. Keeping it minimal for MVP.

---

## Phase 2: Backend Implementation (Modular Design)

### 2.1 Dependencies

**File**: `backend/requirements.txt`

Add:
```
geoip2==4.7.0  # For GeoIP lookups (local database)
maxminddb==2.2.0  # Database reader for GeoIP2
```

**GeoIP Database Setup**:
- Download MaxMind GeoLite2 City database (free): https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
- Requires free MaxMind account registration
- Download `GeoLite2-City.mmdb` file
- Store in `backend/data/GeoLite2-City.mmdb` (or configurable path)
- **No external API calls** - all lookups are local

**Note**: If GeoIP database is not available, the system will gracefully skip geographic data (coordinates will be NULL).

### 2.2 Create Visitor Log Model (MVP)

**File**: `backend/app/models/visitor_log.py`

**Design**: Minimal model matching MVP schema. Can be extended later.

```python
"""
Visitor Log Model (MVP - Minimal Implementation)
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class VisitorLog(Base):
    __tablename__ = "visitor_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Session/User
    session_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Request (Core)
    url = Column(Text, nullable=False)
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Geographic (Core)
    country = Column(String(2))
    country_name = Column(String(100))
    city = Column(String(100))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    
    # Timestamps
    visited_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="visitor_logs")
```

### 2.3 Create GeoIP Service (Modular, Self-Contained)

**File**: `backend/app/services/geoip_service.py`

**Design**: Standalone service that can be reused in other projects. No external dependencies.

```python
"""
GeoIP Service for location lookups (Local Database Only)
Modular design for reusability across projects
"""
import logging
from typing import Optional, Dict
import os
import geoip2.database
import geoip2.errors

logger = logging.getLogger(__name__)


class GeoIPService:
    """
    Service for IP geolocation lookups using local MaxMind GeoLite2 database.
    No external API calls - fully self-contained.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize GeoIP service
        
        Args:
            db_path: Path to MaxMind GeoLite2-City.mmdb file
                    If None, tries default locations or disables GeoIP
        """
        self.reader = None
        
        # Try to find database if path not provided
        if not db_path:
            # Try common locations
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '../../data/GeoLite2-City.mmdb'),
                os.path.join(os.getcwd(), 'data/GeoLite2-City.mmdb'),
                '/usr/local/share/GeoLite2-City.mmdb',
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
        
        if db_path and os.path.exists(db_path):
            try:
                self.reader = geoip2.database.Reader(db_path)
                logger.info(f"GeoIP database loaded from: {db_path}")
            except Exception as e:
                logger.warning(f"Could not load GeoIP database from {db_path}: {e}")
        else:
            logger.warning("GeoIP database not found. Geographic tracking will be disabled.")
    
    def lookup(self, ip_address: str) -> Dict:
        """
        Lookup geographic information for an IP address
        
        Args:
            ip_address: IP address string (IPv4 or IPv6)
        
        Returns:
            Dict with country, city, coordinates, etc.
            Returns None values if lookup fails or database unavailable.
        """
        result = {
            'country': None,
            'country_name': None,
            'city': None,
            'latitude': None,
            'longitude': None,
        }
        
        if not self.reader:
            return result
        
        try:
            response = self.reader.city(ip_address)
            result['country'] = response.country.iso_code
            result['country_name'] = response.country.name
            result['city'] = response.city.name if response.city.name else None
            if response.location.latitude and response.location.longitude:
                result['latitude'] = float(response.location.latitude)
                result['longitude'] = float(response.location.longitude)
        except geoip2.errors.AddressNotFoundError:
            logger.debug(f"IP address not found in database: {ip_address}")
        except Exception as e:
            logger.warning(f"GeoIP lookup error for {ip_address}: {e}")
        
        return result
    
    def is_available(self) -> bool:
        """Check if GeoIP service is available"""
        return self.reader is not None
    
    def close(self):
        """Close the database reader"""
        if self.reader:
            self.reader.close()
            self.reader = None
```

**Configuration**: Add to `backend/app/core/config.py`:
```python
# GeoIP Configuration
GEOIP_DB_PATH: Optional[str] = os.getenv("GEOIP_DB_PATH", None)
```

### 2.4 Create Visitor Tracking Service (Modular)

**File**: `backend/app/services/visitor_tracking.py`

**Design**: Standalone tracking service that can be reused. Loosely coupled from main app.

```python
"""
Visitor Tracking Service (Modular, Reusable)
Can be extracted and reused in other projects
"""
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
import logging

from app.services.geoip_service import GeoIPService
from app.models.visitor_log import VisitorLog

logger = logging.getLogger(__name__)


class VisitorTrackingService:
    """
    Service for tracking visitor analytics.
    Modular design - can be easily extracted to separate module.
    """
    
    def __init__(self, geoip_service: Optional[GeoIPService] = None):
        """
        Initialize tracking service
        
        Args:
            geoip_service: GeoIP service instance (optional, will create if not provided)
        """
        self.geoip_service = geoip_service or GeoIPService()
    
    def _get_ip_address(self, request: Request) -> str:
        """Extract IP address from request, handling proxy headers"""
        ip_address = request.client.host if request.client else "0.0.0.0"
        
        # Handle proxy headers (X-Forwarded-For)
        if 'x-forwarded-for' in request.headers:
            forwarded = request.headers['x-forwarded-for'].split(',')[0].strip()
            if forwarded:
                ip_address = forwarded
        
        return ip_address
    
    def _get_session_id(self, request: Request) -> str:
        """Get or create session ID from cookie"""
        session_id = request.cookies.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
        return session_id
    
    async def track_visit(
        self,
        request: Request,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[VisitorLog]:
        """
        Track a visitor visit
        
        Args:
            request: FastAPI request object
            db: Database session
            user_id: Optional authenticated user ID
        
        Returns:
            VisitorLog instance if successful, None if failed
        """
        try:
            # Get session ID
            session_id_str = self._get_session_id(request)
            session_id = uuid.UUID(session_id_str)
            
            # Get IP address
            ip_address = self._get_ip_address(request)
            
            # Get URL (path + query string)
            url = str(request.url.path)
            if request.url.query:
                url += f"?{request.url.query}"
            
            # Get user agent
            user_agent = request.headers.get('user-agent', '')
            
            # GeoIP lookup (non-blocking, returns None if unavailable)
            geo_data = self.geoip_service.lookup(ip_address) if self.geoip_service.is_available() else {}
            
            # Create visitor log entry
            visitor_log = VisitorLog(
                session_id=session_id,
                user_id=user_id,
                url=url,
                ip_address=ip_address,
                user_agent=user_agent,
                country=geo_data.get('country'),
                country_name=geo_data.get('country_name'),
                city=geo_data.get('city'),
                latitude=geo_data.get('latitude'),
                longitude=geo_data.get('longitude'),
            )
            
            db.add(visitor_log)
            await db.commit()
            await db.refresh(visitor_log)
            
            return visitor_log
            
        except Exception as e:
            logger.error(f"Error tracking visit: {e}", exc_info=True)
            # Don't fail the request if tracking fails
            await db.rollback()
            return None


# Global instance (can be configured per app)
_tracking_service: Optional[VisitorTrackingService] = None


def get_tracking_service() -> VisitorTrackingService:
    """Get or create global tracking service instance"""
    global _tracking_service
    if _tracking_service is None:
        _tracking_service = VisitorTrackingService()
    return _tracking_service
```

### 2.5 Create Analytics API Endpoints

**File**: `backend/app/api/v1/visitor_analytics.py`

```python
"""
Visitor Analytics API Endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.sql import text
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.dependencies import get_current_user_required, get_current_admin
from app.models.visitor_log import VisitorLog
from app.models.user import User

router = APIRouter()


class VisitorLocationResponse(BaseModel):
    latitude: float
    longitude: float
    country: Optional[str]
    country_name: Optional[str]
    city: Optional[str]
    visit_count: int
    unique_visitors: int


class VisitorStatsResponse(BaseModel):
    total_visits: int
    unique_visitors: int
    unique_countries: int
    top_countries: List[dict]
    top_cities: List[dict]
    top_urls: List[dict]
    visits_by_date: List[dict]


@router.get("/locations", response_model=List[VisitorLocationResponse])
async def get_visitor_locations(
    days: int = Query(7, ge=1, le=365),
    min_visits: int = Query(1, ge=1),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get visitor locations for map visualization
    
    Returns aggregated location data with visit counts
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(
        VisitorLog.latitude,
        VisitorLog.longitude,
        VisitorLog.country,
        VisitorLog.country_name,
        VisitorLog.city,
        func.count(VisitorLog.id).label('visit_count'),
        func.count(func.distinct(VisitorLog.session_id)).label('unique_visitors'),
    ).where(
        and_(
            VisitorLog.visited_at >= cutoff_date,
            VisitorLog.latitude.isnot(None),
            VisitorLog.longitude.isnot(None),
        )
    ).group_by(
        VisitorLog.latitude,
        VisitorLog.longitude,
        VisitorLog.country,
        VisitorLog.country_name,
        VisitorLog.city,
    ).having(
        func.count(VisitorLog.id) >= min_visits
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        VisitorLocationResponse(
            latitude=float(row.latitude),
            longitude=float(row.longitude),
            country=row.country,
            country_name=row.country_name,
            city=row.city,
            visit_count=row.visit_count,
            unique_visitors=row.unique_visitors,
        )
        for row in rows
    ]


@router.get("/stats", response_model=VisitorStatsResponse)
async def get_visitor_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated visitor statistics
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total visits
    total_visits_result = await db.execute(
        select(func.count(VisitorLog.id)).where(VisitorLog.visited_at >= cutoff_date)
    )
    total_visits = total_visits_result.scalar() or 0
    
    # Unique visitors
    unique_visitors_result = await db.execute(
        select(func.count(func.distinct(VisitorLog.session_id))).where(
            VisitorLog.visited_at >= cutoff_date
        )
    )
    unique_visitors = unique_visitors_result.scalar() or 0
    
    # Unique countries
    unique_countries_result = await db.execute(
        select(func.count(func.distinct(VisitorLog.country))).where(
            and_(
                VisitorLog.visited_at >= cutoff_date,
                VisitorLog.country.isnot(None),
            )
        )
    )
    unique_countries = unique_countries_result.scalar() or 0
    
    # Top countries
    top_countries_query = select(
        VisitorLog.country,
        VisitorLog.country_name,
        func.count(VisitorLog.id).label('visits'),
        func.count(func.distinct(VisitorLog.session_id)).label('visitors'),
    ).where(
        and_(
            VisitorLog.visited_at >= cutoff_date,
            VisitorLog.country.isnot(None),
        )
    ).group_by(
        VisitorLog.country,
        VisitorLog.country_name,
    ).order_by(
        func.count(VisitorLog.id).desc()
    ).limit(10)
    
    top_countries_result = await db.execute(top_countries_query)
    top_countries = [
        {
            'country': row.country,
            'country_name': row.country_name,
            'visits': row.visits,
            'visitors': row.visitors,
        }
        for row in top_countries_result.all()
    ]
    
    # Top cities
    top_cities_query = select(
        VisitorLog.city,
        VisitorLog.country,
        VisitorLog.country_name,
        func.count(VisitorLog.id).label('visits'),
        func.count(func.distinct(VisitorLog.session_id)).label('visitors'),
    ).where(
        and_(
            VisitorLog.visited_at >= cutoff_date,
            VisitorLog.city.isnot(None),
        )
    ).group_by(
        VisitorLog.city,
        VisitorLog.country,
        VisitorLog.country_name,
    ).order_by(
        func.count(VisitorLog.id).desc()
    ).limit(10)
    
    top_cities_result = await db.execute(top_cities_query)
    top_cities = [
        {
            'city': row.city,
            'country': row.country,
            'country_name': row.country_name,
            'visits': row.visits,
            'visitors': row.visitors,
        }
        for row in top_cities_result.all()
    ]
    
    # Top URLs
    top_urls_query = select(
        VisitorLog.url,
        func.count(VisitorLog.id).label('visits'),
        func.count(func.distinct(VisitorLog.session_id)).label('visitors'),
    ).where(
        VisitorLog.visited_at >= cutoff_date
    ).group_by(
        VisitorLog.url
    ).order_by(
        func.count(VisitorLog.id).desc()
    ).limit(20)
    
    top_urls_result = await db.execute(top_urls_query)
    top_urls = [
        {
            'url': row.url,
            'visits': row.visits,
            'visitors': row.visitors,
        }
        for row in top_urls_result.all()
    ]
    
    # Visits by date
    visits_by_date_query = select(
        func.date(VisitorLog.visited_at).label('date'),
        func.count(VisitorLog.id).label('visits'),
        func.count(func.distinct(VisitorLog.session_id)).label('visitors'),
    ).where(
        VisitorLog.visited_at >= cutoff_date
    ).group_by(
        func.date(VisitorLog.visited_at)
    ).order_by(
        func.date(VisitorLog.visited_at)
    )
    
    visits_by_date_result = await db.execute(visits_by_date_query)
    visits_by_date = [
        {
            'date': row.date.isoformat(),
            'visits': row.visits,
            'visitors': row.visitors,
        }
        for row in visits_by_date_result.all()
    ]
    
    return VisitorStatsResponse(
        total_visits=total_visits,
        unique_visitors=unique_visitors,
        unique_countries=unique_countries,
        top_countries=top_countries,
        top_cities=top_cities,
        top_urls=top_urls,
        visits_by_date=visits_by_date,
    )


@router.get("/recent")
async def get_recent_visits(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent visitor logs with full details (MVP - minimal fields)
    """
    query = select(VisitorLog).order_by(
        VisitorLog.visited_at.desc()
    ).limit(limit)
    
    result = await db.execute(query)
    visits = result.scalars().all()
    
    return [
        {
            'id': str(visit.id),
            'session_id': str(visit.session_id),
            'user_id': str(visit.user_id) if visit.user_id else None,
            'url': visit.url,
            'country': visit.country,
            'country_name': visit.country_name,
            'city': visit.city,
            'latitude': float(visit.latitude) if visit.latitude else None,
            'longitude': float(visit.longitude) if visit.longitude else None,
            'visited_at': visit.visited_at.isoformat(),
        }
        for visit in visits
    ]
```

### 2.6 Register Router

**File**: `backend/app/api/v1/router.py`

Add:
```python
from app.api.v1 import visitor_analytics
api_router.include_router(visitor_analytics.router, prefix="/admin/visitors", tags=["admin", "visitor-analytics"])
```

### 2.6 Register Router

**File**: `backend/app/api/v1/router.py`

Add:
```python
from app.api.v1 import visitor_analytics
api_router.include_router(visitor_analytics.router, prefix="/admin/visitors", tags=["admin", "visitor-analytics"])
```

### 2.7 Add Tracking Middleware to Main App (MVP - Simple Integration)

**File**: `backend/app/main.py`

**MVP Approach**: Simple background task tracking (non-blocking).

```python
from fastapi import Request, BackgroundTasks
from app.services.visitor_tracking import get_tracking_service
from app.core.database import get_db
from app.api.v1.dependencies import get_current_user

@app.middleware("http")
async def track_visitors_middleware(request: Request, call_next, background_tasks: BackgroundTasks):
    """
    Track visitor visits in background (non-blocking)
    Only tracks GET requests to frontend pages (not API calls)
    """
    response = await call_next(request)
    
    # Only track GET requests to frontend routes (skip API routes)
    if request.method == "GET" and not request.url.path.startswith("/api/"):
        # Get user if authenticated (non-blocking check)
        current_user = None
        try:
            # Quick check for auth token without full validation
            if "authorization" in request.headers:
                # You can add a lightweight user check here if needed
                pass
        except:
            pass
        
        # Track in background (non-blocking)
        background_tasks.add_task(
            track_visit_background,
            request,
            current_user
        )
    
    return response


async def track_visit_background(request: Request, user_id=None):
    """Background task for tracking visits"""
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        tracking_service = get_tracking_service()
        await tracking_service.track_visit(request, db, user_id)
```

**Alternative Simple Approach**: Track directly in middleware (synchronous, simpler for MVP):

```python
from app.services.visitor_tracking import get_tracking_service
from app.core.database import async_session_maker

@app.middleware("http")
async def track_visitors_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Track in background (fire and forget)
    if request.method == "GET" and not request.url.path.startswith("/api/"):
        # Use asyncio.create_task for fire-and-forget
        import asyncio
        asyncio.create_task(track_visit_async(request))
    
    return response

async def track_visit_async(request: Request):
    """Async tracking function"""
    async with async_session_maker() as db:
        tracking_service = get_tracking_service()
        await tracking_service.track_visit(request, db, None)
```

---

## Phase 3: Frontend Implementation

### 3.1 Install Map Library

**File**: `frontend/package.json`

Add:
```json
{
  "dependencies": {
    "leaflet": "^1.9.4",
    "vue-leaflet": "^0.8.1"
  }
}
```

Or use a simpler solution like:
- **Leaflet** (open-source, lightweight)
- **Google Maps** (requires API key)
- **Mapbox** (requires API key)

### 3.2 Create Visitor Analytics Tab Component

**File**: `frontend/pages/admin.vue`

Add new tab to existing tabs array:
```typescript
{ id: 'visitorAnalytics', label: 'Visitor Analytics' }
```

### 3.3 Create Map Component

**File**: `frontend/components/VisitorMap.vue`

```vue
<template>
  <div class="visitor-map-container">
    <div id="visitor-map" class="w-full h-96 rounded-lg"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps<{
  locations: Array<{
    latitude: number
    longitude: number
    country?: string
    country_name?: string
    city?: string
    visit_count: number
    unique_visitors: number
  }>
}>()

let map: L.Map | null = null
let markers: L.Marker[] = []

onMounted(() => {
  // Initialize map
  map = L.map('visitor-map').setView([20, 0], 2)
  
  // Add tile layer (OpenStreetMap)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map)
  
  updateMarkers()
})

watch(() => props.locations, () => {
  updateMarkers()
}, { deep: true })

const updateMarkers = () => {
  if (!map) return
  
  // Clear existing markers
  markers.forEach(marker => map!.removeLayer(marker))
  markers = []
  
  // Add new markers
  props.locations.forEach(location => {
    const marker = L.circleMarker(
      [location.latitude, location.longitude],
      {
        radius: Math.min(Math.max(location.visit_count / 10, 5), 30),
        fillColor: '#3b82f6',
        color: '#1e40af',
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.6,
      }
    )
    
    const popupContent = `
      <div class="p-2">
        <div class="font-bold">${location.city || 'Unknown'}, ${location.country_name || location.country || 'Unknown'}</div>
        <div class="text-sm text-gray-600">Visits: ${location.visit_count}</div>
        <div class="text-sm text-gray-600">Unique Visitors: ${location.unique_visitors}</div>
        <div class="text-xs text-gray-500">${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}</div>
      </div>
    `
    
    marker.bindPopup(popupContent)
    marker.addTo(map!)
    markers.push(marker)
  })
  
  // Fit map to show all markers
  if (markers.length > 0) {
    const group = new L.FeatureGroup(markers)
    map.fitBounds(group.getBounds().pad(0.1))
  }
}

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.visitor-map-container {
  width: 100%;
  height: 100%;
}

#visitor-map {
  z-index: 0;
}
</style>
```

### 3.4 Add Visitor Analytics Tab to Admin Page

**File**: `frontend/pages/admin.vue`

Add to the template section (around line 350, after Analytics tab):

```vue
<!-- Visitor Analytics Tab -->
<div v-else-if="activeTab === 'visitorAnalytics'" class="space-y-6">
  <div class="flex items-center justify-between flex-wrap gap-4">
    <h2 class="text-xl font-bold">Visitor Analytics</h2>
    <div class="flex items-center gap-4">
      <select
        v-model="visitorAnalyticsDays"
        class="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
      >
        <option :value="7">Last 7 days</option>
        <option :value="14">Last 14 days</option>
        <option :value="30">Last 30 days</option>
        <option :value="60">Last 60 days</option>
        <option :value="90">Last 90 days</option>
      </select>
      <button
        @click="loadVisitorAnalytics"
        :disabled="visitorAnalyticsLoading"
        class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm"
      >
        {{ visitorAnalyticsLoading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>
  </div>

  <!-- Loading -->
  <div v-if="visitorAnalyticsLoading && !visitorAnalyticsData" class="text-center py-8 text-gray-400">
    Loading visitor analytics...
  </div>

  <!-- Summary Cards -->
  <div v-if="visitorAnalyticsData" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="bg-gray-900 rounded-lg p-6">
      <div class="text-sm text-gray-400 mb-1">Total Visits</div>
      <div class="text-2xl font-bold">{{ visitorAnalyticsData.total_visits?.toLocaleString() || 0 }}</div>
    </div>
    <div class="bg-gray-900 rounded-lg p-6">
      <div class="text-sm text-gray-400 mb-1">Unique Visitors</div>
      <div class="text-2xl font-bold">{{ visitorAnalyticsData.unique_visitors?.toLocaleString() || 0 }}</div>
    </div>
    <div class="bg-gray-900 rounded-lg p-6">
      <div class="text-sm text-gray-400 mb-1">Countries</div>
      <div class="text-2xl font-bold">{{ visitorAnalyticsData.unique_countries || 0 }}</div>
    </div>
    <div class="bg-gray-900 rounded-lg p-6">
      <div class="text-sm text-gray-400 mb-1">Locations Tracked</div>
      <div class="text-2xl font-bold">{{ visitorLocations?.length || 0 }}</div>
    </div>
  </div>

  <!-- Map Visualization -->
  <div v-if="visitorLocations && visitorLocations.length > 0" class="bg-gray-900 rounded-lg p-6">
    <h3 class="text-lg font-bold mb-4">Visitor Locations Map</h3>
    <VisitorMap :locations="visitorLocations" />
  </div>

  <!-- Top Countries -->
  <div v-if="visitorAnalyticsData?.top_countries" class="bg-gray-900 rounded-lg p-6">
    <h3 class="text-lg font-bold mb-4">Top Countries</h3>
    <div class="space-y-2">
      <div
        v-for="(country, index) in visitorAnalyticsData.top_countries"
        :key="country.country"
        class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
      >
        <div class="flex items-center gap-3">
          <span class="text-gray-500 text-sm w-6">#{{ index + 1 }}</span>
          <span class="text-white">{{ country.country_name || country.country }}</span>
        </div>
        <div class="text-right">
          <div class="text-sm font-bold">{{ country.visits.toLocaleString() }} visits</div>
          <div class="text-xs text-gray-500">{{ country.visitors }} visitors</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Top Cities -->
  <div v-if="visitorAnalyticsData?.top_cities" class="bg-gray-900 rounded-lg p-6">
    <h3 class="text-lg font-bold mb-4">Top Cities</h3>
    <div class="space-y-2">
      <div
        v-for="(city, index) in visitorAnalyticsData.top_cities"
        :key="`${city.city}-${city.country}`"
        class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
      >
        <div class="flex items-center gap-3">
          <span class="text-gray-500 text-sm w-6">#{{ index + 1 }}</span>
          <span class="text-white">{{ city.city }}, {{ city.country_name || city.country }}</span>
        </div>
        <div class="text-right">
          <div class="text-sm font-bold">{{ city.visits.toLocaleString() }} visits</div>
          <div class="text-xs text-gray-500">{{ city.visitors }} visitors</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Top URLs -->
  <div v-if="visitorAnalyticsData?.top_urls" class="bg-gray-900 rounded-lg p-6">
    <h3 class="text-lg font-bold mb-4">Most Visited URLs</h3>
    <div class="space-y-2">
      <div
        v-for="(url, index) in visitorAnalyticsData.top_urls"
        :key="url.url"
        class="flex items-center justify-between p-2 hover:bg-gray-800 rounded"
      >
        <div class="flex items-center gap-3 flex-1 min-w-0">
          <span class="text-gray-500 text-sm w-6">#{{ index + 1 }}</span>
          <span class="text-white text-sm truncate">{{ url.url }}</span>
        </div>
        <div class="text-right flex-shrink-0 ml-4">
          <div class="text-sm font-bold">{{ url.visits.toLocaleString() }} visits</div>
          <div class="text-xs text-gray-500">{{ url.visitors }} visitors</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Recent Visits Table -->
  <div v-if="recentVisits && recentVisits.length > 0" class="bg-gray-900 rounded-lg overflow-hidden">
    <h3 class="text-lg font-bold mb-4 p-6 pb-0">Recent Visits</h3>
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="bg-gray-800">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Time</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">URL</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Location</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">User</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-800">
          <tr v-for="visit in recentVisits" :key="visit.id" class="hover:bg-gray-800">
            <td class="px-4 py-3 text-sm text-gray-300">
              {{ formatDate(visit.visited_at) }}
            </td>
            <td class="px-4 py-3 text-sm text-gray-300 truncate max-w-xs">
              {{ visit.url }}
            </td>
            <td class="px-4 py-3 text-sm text-gray-300">
              <div v-if="visit.city || visit.country_name">
                {{ visit.city }}{{ visit.city && visit.country_name ? ', ' : '' }}{{ visit.country_name }}
              </div>
              <div v-else class="text-gray-500">Unknown</div>
            </td>
            <td class="px-4 py-3 text-sm text-gray-300">
              {{ visit.user_id ? 'Authenticated' : 'Anonymous' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
```

Add to script section:

```typescript
// Visitor Analytics
const visitorAnalyticsData = ref<any | null>(null)
const visitorLocations = ref<any[]>([])
const recentVisits = ref<any[]>([])
const visitorAnalyticsLoading = ref(false)
const visitorAnalyticsDays = ref(30)

const loadVisitorAnalytics = async () => {
  visitorAnalyticsLoading.value = true
  try {
    // Load stats
    const statsResponse = await api.get(`/admin/visitors/stats?days=${visitorAnalyticsDays.value}`)
    visitorAnalyticsData.value = statsResponse
    
    // Load locations for map
    const locationsResponse = await api.get(`/admin/visitors/locations?days=${visitorAnalyticsDays.value}`)
    visitorLocations.value = locationsResponse
    
    // Load recent visits
    const recentResponse = await api.get('/admin/visitors/recent?limit=50')
    recentVisits.value = recentResponse
  } catch (err: any) {
    console.error('Failed to load visitor analytics:', err)
    error.value = err.message || 'Failed to load visitor analytics'
  } finally {
    visitorAnalyticsLoading.value = false
  }
}

// Add to watch for tab changes
watch(activeTab, (newTab) => {
  // ... existing watches
  else if (newTab === 'visitorAnalytics') {
    loadVisitorAnalytics()
  }
})
```

---

## Phase 4: Module Reusability Design

### 4.1 Modular Structure

The analytics module is designed to be loosely coupled and reusable:

```
backend/app/
├── services/
│   ├── geoip_service.py          # Standalone GeoIP service
│   └── visitor_tracking.py        # Standalone tracking service
├── models/
│   └── visitor_log.py             # Database model
└── api/v1/
    └── visitor_analytics.py       # API endpoints
```

**Key Design Principles**:
- **Services are independent**: Can be used without the full app
- **No hard dependencies**: Services accept dependencies via constructor
- **Configurable**: Paths and settings via environment/config
- **Easy extraction**: Can be moved to separate package/module

### 4.2 Reusing in Other Projects

To reuse this module in another project:

1. **Copy the services**:
   - `geoip_service.py` → Standalone, no dependencies on app
   - `visitor_tracking.py` → Only depends on GeoIP service and models

2. **Copy the model**:
   - `visitor_log.py` → Standard SQLAlchemy model

3. **Copy the API** (optional):
   - `visitor_analytics.py` → FastAPI endpoints

4. **Configure**:
   - Set `GEOIP_DB_PATH` environment variable
   - Add database migration
   - Integrate tracking middleware

**Example Integration**:
```python
# In any FastAPI app
from visitor_analytics import VisitorTrackingService, GeoIPService

geoip = GeoIPService(db_path="/path/to/GeoLite2-City.mmdb")
tracking = VisitorTrackingService(geoip_service=geoip)

# Use in middleware
@app.middleware("http")
async def track_visits(request: Request, call_next):
    response = await call_next(request)
    # Track visit
    await tracking.track_visit(request, db, user_id)
    return response
```

---

## Phase 5: Performance Optimization (MVP - Minimal)

### 5.1 Database Indexing

Essential indexes are included in the MVP schema. Additional indexes can be added based on query patterns.

### 5.2 GeoIP Lookup Optimization

- GeoIP lookups are fast (local database)
- Consider caching frequently accessed IPs if needed (future enhancement)
- Database file is read-only, safe for concurrent access

**Note**: For MVP, no caching layer is needed. GeoIP lookups are fast enough.

---

## Phase 6: Testing (MVP)

### 6.1 Manual Testing Checklist

- [ ] Verify tracking works on frontend routes
- [ ] Verify API routes are NOT tracked
- [ ] Test map visualization with sample data
- [ ] Verify admin access controls
- [ ] Test GeoIP lookup (with and without database)
- [ ] Verify analytics endpoints return correct data

### 6.2 Basic Unit Tests (Optional for MVP)

- Test GeoIP service lookup
- Test tracking service
- Test analytics queries

---

## Implementation Checklist (MVP)

### Backend
- [ ] Create database migration for `visitor_logs` table
- [ ] Add GeoIP dependencies to requirements.txt (`geoip2`, `maxminddb`)
- [ ] Create VisitorLog model (minimal schema)
- [ ] Create GeoIP service (modular, reusable)
- [ ] Create visitor tracking service (modular, reusable)
- [ ] Create analytics API endpoints
- [ ] Register router in `router.py`
- [ ] Add tracking middleware to `main.py`
- [ ] Test endpoints manually

### Frontend
- [ ] Install Leaflet: `npm install leaflet`
- [ ] Create VisitorMap component
- [ ] Add "Visitor Analytics" tab to admin page
- [ ] Add API calls for analytics data
- [ ] Test map rendering
- [ ] Test data display

### Infrastructure (Minimal)
- [ ] Download MaxMind GeoLite2-City.mmdb (free, requires account)
- [ ] Place database file in `backend/data/` or configure path
- [ ] Set `GEOIP_DB_PATH` environment variable (optional)
- [ ] Update docker-compose.yml to mount GeoIP database (if using volume)
- [ ] Update backend Dockerfile to copy GeoIP database (if using COPY)
- [ ] Update docker-compose.yml to mount GeoIP database (if using volume)
- [ ] Update backend Dockerfile to copy GeoIP database (if using COPY)

### Documentation
- [ ] Document module structure for reusability
- [ ] Document configuration options

---

## Future Enhancements

1. **Real-time Updates**: WebSocket for live visitor tracking
2. **Heat Maps**: Show visit density on map
3. **User Journeys**: Track user paths through the site
4. **Device Analytics**: Detailed device/browser breakdown
5. **Referrer Tracking**: Track where visitors come from
6. **Export Functionality**: Export analytics data to CSV/JSON
7. **Custom Date Ranges**: Allow custom date range selection
8. **Filtering**: Filter by country, city, URL, etc.
9. **Charts**: Add time-series charts for visit trends
10. **Alerts**: Set up alerts for unusual traffic patterns

---

## Deployment Architecture

### MVP: Integrated into Main Backend Container

**Current Plan**: Analytics runs as part of the main `backend` container.

**Why this approach for MVP**:
- ✅ Simpler deployment (no additional containers)
- ✅ Shared database connection (no network overhead)
- ✅ Lower resource usage
- ✅ Easier to develop and debug
- ✅ Fits existing docker-compose structure

**Docker Setup**:
- Analytics code lives in `backend/app/` alongside other code
- GeoIP database file mounted as volume or copied into image
- Same container, same database, same network

**Dockerfile Update** (if needed):
```dockerfile
# Add GeoIP database to backend container
COPY data/GeoLite2-City.mmdb /app/data/GeoLite2-City.mmdb
# Or mount as volume in docker-compose.yml
```

**docker-compose.yml Update**:
```yaml
backend:
  volumes:
    - ./backend:/app
    - ./backend/data/GeoLite2-City.mmdb:/app/data/GeoLite2-City.mmdb:ro  # GeoIP DB
  environment:
    GEOIP_DB_PATH: /app/data/GeoLite2-City.mmdb
```

### Alternative: Separate Container (Future Enhancement)

If you want it as a separate microservice container:

**Pros**:
- ✅ True separation of concerns
- ✅ Can scale independently
- ✅ Can be deployed separately
- ✅ Easier to extract/reuse in other projects

**Cons**:
- ❌ More complex setup
- ❌ Additional container overhead
- ❌ Network latency between services
- ❌ More configuration needed

**Separate Container Structure** (if needed later):
```
docker-compose.yml:
  - backend (main app)
  - analytics (visitor tracking service)
  - postgres (shared database)
```

**For MVP**: Keep it integrated. Can extract later if needed.

---

## Notes & Configuration

### GeoIP Database Setup

1. **Register for MaxMind account** (free): https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
2. **Download GeoLite2-City.mmdb** (binary database file)
3. **Place file** in `backend/data/GeoLite2-City.mmdb` or configure path via `GEOIP_DB_PATH`
4. **Update database periodically** (MaxMind updates monthly)

### Docker Volume for GeoIP Database

**Option 1: Copy into image** (recommended for production):
```dockerfile
# In backend/Dockerfile
COPY data/GeoLite2-City.mmdb /app/data/GeoLite2-City.mmdb
```

**Option 2: Mount as volume** (recommended for development):
```yaml
# In docker-compose.yml
backend:
  volumes:
    - ./backend/data/GeoLite2-City.mmdb:/app/data/GeoLite2-City.mmdb:ro
```

### Module Reusability

The analytics module is designed to be:
- **Standalone**: Services can work independently
- **Configurable**: No hard-coded paths or dependencies
- **Extractable**: Can be moved to separate package
- **Framework-agnostic**: Services don't depend on FastAPI specifics (except Request object)

### Performance Notes

- **GeoIP lookups**: Fast (local database, ~1ms per lookup)
- **Tracking**: Non-blocking (background tasks)
- **Database**: Indexed for common queries
- **Scalability**: For high traffic, consider message queue (future enhancement)

### MVP Scope

This plan focuses on **minimal viable implementation**:
- Core features only (location, URL tracking, map)
- No external API dependencies
- No complex privacy features
- Simple, maintainable code
- Easy to extend later

