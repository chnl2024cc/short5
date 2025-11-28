"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, videos, feed

api_router = APIRouter()

# Register route modules
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(feed.router, prefix="/feed", tags=["feed"])
# api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

