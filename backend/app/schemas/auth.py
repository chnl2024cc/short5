"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: str
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

