"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr


class UserCreate(UserBase):
    # Using bcrypt_sha256 allows passwords of any length (no 72-byte limit)
    # Still enforce reasonable min/max for security and UX
    password: str = Field(..., min_length=8, max_length=200)
    session_id: Optional[str] = None  # For merging anonymous votes


class UserResponse(UserBase):
    id: str
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    videos_uploaded: int = 0
    total_likes_received: int = 0
    total_views: int = 0


class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: str
    is_admin: bool = False
    created_at: Optional[str] = None
    stats: UserStats

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    session_id: Optional[str] = None  # For merging anonymous votes


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str

