"""
API Dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current authenticated user (optional)"""
    import logging
    logger = logging.getLogger(__name__)
    
    if not credentials:
        logger.warning("No credentials provided in request - HTTPBearer returned None")
        return None
    
    token = credentials.credentials
    logger.info(f"Received token: {token[:30]}... (length: {len(token)})")
    
    payload = decode_token(token)
    
    if payload is None:
        logger.warning(f"Token decode failed for token: {token[:30]}...")
        return None
    
    logger.info(f"Token decoded successfully. Payload keys: {list(payload.keys())}, type: {payload.get('type')}")
    
    if payload.get("type") != "access":
        logger.warning(f"Token type mismatch. Expected 'access', got: {payload.get('type')}")
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("No user_id in token payload")
        return None
    
    logger.info(f"Looking up user with ID: {user_id}")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        logger.warning(f"User not found for user_id: {user_id}")
        return None
    
    if not user.is_active:
        logger.warning(f"User {user_id} is inactive")
        return None
    
    logger.info(f"User authenticated successfully: {user.username} (ID: {user.id})")
    return user


def get_current_user_required(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Get current user (required, raises 401 if not authenticated)"""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """Get current user, ensuring they are an admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
