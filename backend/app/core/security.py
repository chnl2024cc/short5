"""
Security utilities: JWT, password hashing
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.hash import bcrypt_sha256

from app.core.config import settings

# Use bcrypt_sha256 directly (not through CryptContext) to ensure it's used
# bcrypt_sha256 pre-hashes with SHA-256 before bcrypt, allowing unlimited password length
# This is the recommended approach per passlib documentation

# Pre-initialize backend with a short password to avoid detection phase errors
# bcrypt 5.0.0+ raises errors for passwords > 72 bytes during backend detection
# Using a short password here triggers initialization without hitting the limit
try:
    _ = bcrypt_sha256.hash("init")
except Exception:
    # If initialization fails, continue - will be handled on first real use
    pass


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash using bcrypt_sha256"""
    # Ensure password is a string
    if isinstance(plain_password, bytes):
        plain_password = plain_password.decode('utf-8')
    
    # Use bcrypt_sha256 directly - handles passwords of any length
    return bcrypt_sha256.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt_sha256 (handles passwords of any length)"""
    # Ensure password is a string
    if isinstance(password, bytes):
        password = password.decode('utf-8')
    
    # Use bcrypt_sha256 directly - it pre-hashes with SHA-256 before bcrypt
    # This allows passwords of any length without the 72-byte limit
    # This is the recommended approach per passlib documentation
    return bcrypt_sha256.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"JWT decode error: {type(e).__name__}: {str(e)}")
        return None
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error decoding token: {type(e).__name__}: {str(e)}")
        return None

