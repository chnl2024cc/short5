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


class UserResponse(UserBase):
    id: str
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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

