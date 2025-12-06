"""
FastAPI Main Application
"""
import logging
import traceback
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Short5 Platform API",
    description="Backend API for Short5 Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
# Use configured origins (supports both development and production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Serve static files for processed videos (development mode)
# This serves both uploaded files and processed files (MP4s, thumbnails)
# Use absolute path to ensure it works regardless of working directory
uploads_dir = Path("/app/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
    logger.info(f"Serving static files from: {uploads_dir.absolute()}")
else:
    logger.warning(f"Uploads directory not found: {uploads_dir.absolute()}")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc) if settings.ENVIRONMENT == "development" else "Internal server error",
                "details": traceback.format_exc() if settings.ENVIRONMENT == "development" else None,
            }
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": str(exc) if settings.ENVIRONMENT == "development" else "Database error occurred",
                "details": traceback.format_exc() if settings.ENVIRONMENT == "development" else None,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": exc.errors(),
            }
        },
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        from app.core.database import engine, Base, AsyncSessionLocal
        from app.models import user, video, vote, view, user_liked_video
        from sqlalchemy import text
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
        
        # Ensure error_reason column exists (migration)
        try:
            async with AsyncSessionLocal() as db:
                # Check if column exists
                result = await db.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'videos' 
                        AND column_name = 'error_reason'
                    )
                """))
                if not result.scalar():
                    logger.info("Adding error_reason column to videos table...")
                    await db.execute(text("ALTER TABLE videos ADD COLUMN error_reason TEXT;"))
                    await db.commit()
                    logger.info("✓ error_reason column added successfully")
                else:
                    logger.info("✓ error_reason column already exists")
        except Exception as e:
            logger.warning(f"Could not verify/add error_reason column: {e}")
            # Don't fail startup if migration fails
        
        # Ensure video_metadata_json column exists (migration)
        try:
            async with AsyncSessionLocal() as db:
                # Check if column exists
                result = await db.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'videos' 
                        AND column_name = 'video_metadata_json'
                    )
                """))
                if not result.scalar():
                    logger.info("Adding video_metadata_json column to videos table...")
                    await db.execute(text("ALTER TABLE videos ADD COLUMN video_metadata_json TEXT;"))
                    await db.commit()
                    logger.info("✓ video_metadata_json column added successfully")
                else:
                    logger.info("✓ video_metadata_json column already exists")
        except Exception as e:
            logger.warning(f"Could not verify/add video_metadata_json column: {e}")
            # Don't fail startup if migration fails
        
        # Migrate votes table to support anonymous votes
        try:
            async with AsyncSessionLocal() as db:
                # Check if session_id column exists
                result = await db.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'votes' 
                        AND column_name = 'session_id'
                    )
                """))
                if not result.scalar():
                    logger.info("Migrating votes table to support anonymous votes...")
                    
                    # Drop old unique constraint if it exists
                    try:
                        await db.execute(text("ALTER TABLE votes DROP CONSTRAINT IF EXISTS votes_user_id_video_id_key;"))
                    except Exception:
                        pass  # Constraint might not exist
                    
                    # Make user_id nullable
                    await db.execute(text("ALTER TABLE votes ALTER COLUMN user_id DROP NOT NULL;"))
                    
                    # Add session_id column
                    await db.execute(text("ALTER TABLE votes ADD COLUMN session_id UUID;"))
                    
                    # Add check constraint
                    await db.execute(text("""
                        ALTER TABLE votes ADD CONSTRAINT check_user_or_session 
                        CHECK ((user_id IS NOT NULL AND session_id IS NULL) OR (user_id IS NULL AND session_id IS NOT NULL));
                    """))
                    
                    # Create partial unique indexes
                    # For authenticated votes: unique on (user_id, video_id)
                    await db.execute(text("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_votes_user_video_unique 
                        ON votes (user_id, video_id) 
                        WHERE user_id IS NOT NULL;
                    """))
                    
                    # For anonymous votes: unique on (session_id, video_id)
                    await db.execute(text("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_votes_session_video_unique 
                        ON votes (session_id, video_id) 
                        WHERE session_id IS NOT NULL;
                    """))
                    
                    # Add index on session_id
                    await db.execute(text("CREATE INDEX IF NOT EXISTS idx_votes_session_id ON votes(session_id);"))
                    
                    await db.commit()
                    logger.info("✓ votes table migration completed successfully")
                else:
                    logger.info("✓ votes table already migrated")
        except Exception as e:
            logger.warning(f"Could not migrate votes table: {e}", exc_info=True)
            # Don't fail startup if migration fails
            
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}", exc_info=True)
        # Don't raise - allow app to start even if tables exist


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        
        # Test database connection
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        
        return JSONResponse(
            content={
                "status": "healthy",
                "service": "short-video-platform-api",
                "database": "connected",
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "short-video-platform-api",
                "database": "disconnected",
                "error": str(e) if settings.ENVIRONMENT == "development" else None,
            }
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Short5 Platform API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

