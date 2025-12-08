"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, videos, feed, reports, share_analytics, visitor_analytics

api_router = APIRouter()

# Register route modules
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(feed.router, prefix="/feed", tags=["feed"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(share_analytics.router, prefix="/admin/shares", tags=["admin", "share-analytics"])
api_router.include_router(visitor_analytics.router, prefix="/admin/visitors", tags=["admin", "visitor-analytics"])
from app.api.v1 import admin
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

