"""
Authentication Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import timedelta
from typing import Optional
import uuid
import logging

from app.core.database import get_db
from app.api.v1.dependencies import get_current_user_required
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from app.models.user import User
from app.models.vote import Vote, VoteDirection
from app.models.user_liked_video import UserLikedVideo
from app.schemas.auth import (
    UserCreate,
    LoginRequest,
    AuthResponse,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def merge_anonymous_votes(user_id: uuid.UUID, session_id: str, db: AsyncSession) -> int:
    """
    Merge anonymous votes (identified by session_id) into user's account.
    
    Args:
        user_id: The authenticated user's ID
        session_id: The session ID from anonymous votes
        db: Database session
    
    Returns:
        Number of votes merged
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        logger.warning(f"Invalid session_id format: {session_id}")
        return 0
    
    # Find all anonymous votes with this session_id
    result = await db.execute(
        select(Vote).where(Vote.session_id == session_uuid)
    )
    anonymous_votes = result.scalars().all()
    
    if not anonymous_votes:
        return 0
    
    merged_count = 0
    
    for anonymous_vote in anonymous_votes:
        # Check if user already voted on this video
        existing_vote_result = await db.execute(
            select(Vote).where(
                Vote.user_id == user_id,
                Vote.video_id == anonymous_vote.video_id,
            )
        )
        existing_vote = existing_vote_result.scalar_one_or_none()
        
        if existing_vote:
            # User already voted - keep the authenticated vote, delete anonymous one
            # If anonymous vote was a like and user's vote is different, we could update,
            # but for simplicity, we keep the authenticated vote
            delete_stmt = delete(Vote).where(Vote.id == anonymous_vote.id)
            await db.execute(delete_stmt)
        else:
            # No existing vote - transfer anonymous vote to user
            anonymous_vote.user_id = user_id
            anonymous_vote.session_id = None
            
            # If it was a like, also add to UserLikedVideo
            if anonymous_vote.direction == VoteDirection.LIKE:
                # Check if already in liked videos
                existing_liked_result = await db.execute(
                    select(UserLikedVideo).where(
                        UserLikedVideo.user_id == user_id,
                        UserLikedVideo.video_id == anonymous_vote.video_id,
                    )
                )
                if not existing_liked_result.scalar_one_or_none():
                    liked_video = UserLikedVideo(
                        user_id=user_id,
                        video_id=anonymous_vote.video_id,
                    )
                    db.add(liked_video)
            
            merged_count += 1
    
    try:
        await db.commit()
        logger.info(f"Merged {merged_count} anonymous votes for user {user_id}")
        return merged_count
    except Exception as e:
        await db.rollback()
        logger.error(f"Error merging anonymous votes: {e}", exc_info=True)
        return 0


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user"""
    try:
        # Check if username exists
        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )
        
        # Check if email exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )
        
        # Password validation is handled by the schema (min_length=8)
        # bcrypt_sha256 can handle passwords of any length, so no byte limit check needed
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Merge anonymous votes if session_id provided
        if user_data.session_id:
            await merge_anonymous_votes(user.id, user_data.session_id, db)
        
        return AuthResponse(
            user=UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                is_admin=user.is_admin,
                created_at=user.created_at,
            ),
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password"""
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Merge anonymous votes if session_id provided
    if login_data.session_id:
        await merge_anonymous_votes(user.id, login_data.session_id, db)
    
    return AuthResponse(
        user=UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            is_admin=user.is_admin,
            created_at=user.created_at,
        ),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
):
    """Refresh access token"""
    payload = decode_token(refresh_data.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout")
async def logout():
    """Logout (client should discard tokens)"""
    return {"message": "Logged out successfully"}

