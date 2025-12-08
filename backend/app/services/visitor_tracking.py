"""
Visitor Tracking Service (Modular, Reusable)
Can be extracted and reused in other projects
"""
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
import logging

from app.services.geoip_service import GeoIPService
from app.models.visitor_log import VisitorLog

logger = logging.getLogger(__name__)


class VisitorTrackingService:
    """
    Service for tracking visitor analytics.
    Modular design - can be easily extracted to separate module.
    """
    
    def __init__(self, geoip_service: Optional[GeoIPService] = None):
        """
        Initialize tracking service
        
        Args:
            geoip_service: GeoIP service instance (optional, will create if not provided)
        """
        self.geoip_service = geoip_service or GeoIPService()
    
    def _get_ip_address(self, request: Request) -> str:
        """Extract IP address from request, handling proxy headers"""
        ip_address = request.client.host if request.client else "0.0.0.0"
        
        # Handle proxy headers (X-Forwarded-For)
        if 'x-forwarded-for' in request.headers:
            forwarded = request.headers['x-forwarded-for'].split(',')[0].strip()
            if forwarded:
                ip_address = forwarded
        
        # Log if it's a localhost/private IP (won't have geo data)
        if ip_address in ('127.0.0.1', '::1', 'localhost') or ip_address.startswith('192.168.') or ip_address.startswith('10.') or ip_address.startswith('172.'):
            logger.debug(f"Tracking localhost/private IP: {ip_address} (will not have geo data)")
        
        return ip_address
    
    def _get_session_id(self, request: Request) -> str:
        """Get or create session ID from cookie"""
        session_id = request.cookies.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
        return session_id
    
    async def track_visit(
        self,
        request: Request,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[VisitorLog]:
        """
        Track a visitor visit
        
        Args:
            request: FastAPI request object
            db: Database session
            user_id: Optional authenticated user ID
        
        Returns:
            VisitorLog instance if successful, None if failed
        """
        try:
            # Get session ID
            session_id_str = self._get_session_id(request)
            session_id = uuid.UUID(session_id_str)
            
            # Get IP address
            ip_address = self._get_ip_address(request)
            
            # Get URL (path + query string)
            url = str(request.url.path)
            if request.url.query:
                url += f"?{request.url.query}"
            
            # Get user agent
            user_agent = request.headers.get('user-agent', '')
            
            # GeoIP lookup (lazy-loaded, only loads database when lookup is actually called)
            # Skip availability check to avoid loading database unnecessarily
            # The lookup method itself handles lazy loading
            geo_data = self.geoip_service.lookup(ip_address)
            
            # Log for debugging
            if not geo_data.get('country') and not geo_data.get('city'):
                logger.warning(f"No geo data found for IP: {ip_address}. GeoIP service available: {self.geoip_service.is_available()}. "
                             f"This is normal for localhost (127.0.0.1) or private IP addresses.")
            
            # Create visitor log entry
            visitor_log = VisitorLog(
                session_id=session_id,
                user_id=user_id,
                url=url,
                ip_address=ip_address,
                user_agent=user_agent,
                country=geo_data.get('country'),
                country_name=geo_data.get('country_name'),
                city=geo_data.get('city'),
                latitude=geo_data.get('latitude'),
                longitude=geo_data.get('longitude'),
            )
            
            db.add(visitor_log)
            await db.commit()
            await db.refresh(visitor_log)
            
            return visitor_log
            
        except Exception as e:
            logger.error(f"Error tracking visit: {e}", exc_info=True)
            # Don't fail the request if tracking fails
            await db.rollback()
            return None


# Global instance (can be configured per app)
_tracking_service: Optional[VisitorTrackingService] = None


def get_tracking_service() -> VisitorTrackingService:
    """Get or create global tracking service instance"""
    global _tracking_service
    if _tracking_service is None:
        from app.core.config import settings
        geoip_service = GeoIPService(db_path=settings.GEOIP_DB_PATH)
        _tracking_service = VisitorTrackingService(geoip_service=geoip_service)
    return _tracking_service

