"""
Visitor Analytics API Endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin_user
from app.models.visitor_log import VisitorLog
from app.models.user import User

router = APIRouter()


class VisitorLocationResponse(BaseModel):
    latitude: float
    longitude: float
    country: str | None
    country_name: str | None
    city: str | None
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
    current_user: User = Depends(get_current_admin_user),
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
    current_user: User = Depends(get_current_admin_user),
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
    current_user: User = Depends(get_current_admin_user),
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

