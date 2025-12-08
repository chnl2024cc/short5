"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field, model_validator
from typing import List, Union


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://short5_user:short5_password@localhost:5432/short5_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Backend
    # Read from BACKEND_BASE_URL environment variable
    # Default is for development only. In production, this MUST be set via environment variable.
    BACKEND_BASE_URL: str = Field(
        default="http://localhost:8000",
        description="Base URL for the backend API. Must be set via BACKEND_BASE_URL env var in production."
    )
    
    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-use-strong-random-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8080,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:8080,http://127.0.0.1:5173"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else ["http://localhost:3000", "http://localhost:8080"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_VIDEO_FORMATS: List[str] = [".mp4", ".mov", ".avi"]
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # GeoIP (Visitor Analytics)
    # Supports both MaxMind GeoLite2-City.mmdb and DB-IP dbip-city-lite databases
    # Both use the same .mmdb format and are compatible with geoip2 library
    # REQUIRED: Set via GEOIP_DB_PATH environment variable for geographic tracking
    GEOIP_DB_PATH: str | None = None  # Path to GeoIP database file (.mmdb format)
    
    # Environment
    ENVIRONMENT: str = "development"
    
    @model_validator(mode="after")
    def validate_production_settings(self):
        """Validate that production/staging environments have proper configuration"""
        if self.ENVIRONMENT in ("production", "staging"):
            # Check if BACKEND_BASE_URL is empty, localhost, or not properly set
            if (not self.BACKEND_BASE_URL or 
                self.BACKEND_BASE_URL.strip() == "" or
                "localhost" in self.BACKEND_BASE_URL.lower() or
                "127.0.0.1" in self.BACKEND_BASE_URL):
                raise ValueError(
                    f"BACKEND_BASE_URL must be set via environment variable in {self.ENVIRONMENT} environment. "
                    f"Current value: '{self.BACKEND_BASE_URL}'. "
                    "Using localhost or empty value is not allowed in production/staging. "
                    "Please set BACKEND_BASE_URL to your production backend URL (e.g., https://api.yourdomain.com)."
                )
        return self
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from environment


settings = Settings()

