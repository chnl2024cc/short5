"""
GeoIP Service for location lookups (Local Database Only)
Modular design for reusability across projects
"""
import logging
from typing import Optional, Dict
import os
import geoip2.database
import geoip2.errors

logger = logging.getLogger(__name__)


class GeoIPService:
    """
    Service for IP geolocation lookups using local MaxMind GeoLite2 database.
    No external API calls - fully self-contained.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize GeoIP service (lazy loading - database not loaded until first lookup)
        
        Args:
            db_path: Path to MaxMind GeoLite2-City.mmdb file
                    If None, tries default locations or disables GeoIP
        """
        self.reader = None
        self._db_path = db_path
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization - only load database when actually needed"""
        if self._initialized:
            return
        
        self._initialized = True
        db_path = self._db_path
        
        # Try to find database if path not provided
        if not db_path:
            # Try common locations
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '../../data/GeoLite2-City.mmdb'),
                os.path.join(os.getcwd(), 'data/GeoLite2-City.mmdb'),
                os.path.join(os.getcwd(), 'backend/data/GeoLite2-City.mmdb'),
                '/app/data/GeoLite2-City.mmdb',  # Docker container path
                '/usr/local/share/GeoLite2-City.mmdb',
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
        
        if db_path and os.path.exists(db_path):
            try:
                self.reader = geoip2.database.Reader(db_path)
                logger.info(f"GeoIP database loaded from: {db_path}")
            except Exception as e:
                logger.warning(f"Could not load GeoIP database from {db_path}: {e}")
        else:
            logger.debug("GeoIP database not found. Geographic tracking will be disabled.")
    
    def lookup(self, ip_address: str) -> Dict:
        """
        Lookup geographic information for an IP address
        
        Args:
            ip_address: IP address string (IPv4 or IPv6)
        
        Returns:
            Dict with country, city, coordinates, etc.
            Returns None values if lookup fails or database unavailable.
        """
        # Lazy initialization - only load database when lookup is actually called
        self._ensure_initialized()
        
        result = {
            'country': None,
            'country_name': None,
            'city': None,
            'latitude': None,
            'longitude': None,
        }
        
        if not self.reader:
            return result
        
        try:
            response = self.reader.city(ip_address)
            result['country'] = response.country.iso_code
            result['country_name'] = response.country.name
            result['city'] = response.city.name if response.city.name else None
            if response.location.latitude and response.location.longitude:
                result['latitude'] = float(response.location.latitude)
                result['longitude'] = float(response.location.longitude)
        except geoip2.errors.AddressNotFoundError:
            logger.debug(f"IP address not found in database: {ip_address}")
        except Exception as e:
            logger.warning(f"GeoIP lookup error for {ip_address}: {e}")
        
        return result
    
    def is_available(self) -> bool:
        """Check if GeoIP service is available (lazy check - doesn't load database)"""
        if not self._initialized:
            # Check if database file exists without loading it
            db_path = self._db_path
            if not db_path:
                possible_paths = [
                    os.path.join(os.path.dirname(__file__), '../../data/GeoLite2-City.mmdb'),
                    os.path.join(os.getcwd(), 'data/GeoLite2-City.mmdb'),
                    os.path.join(os.getcwd(), 'backend/data/GeoLite2-City.mmdb'),
                    '/app/data/GeoLite2-City.mmdb',
                    '/usr/local/share/GeoLite2-City.mmdb',
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        return True
                return False
            return os.path.exists(db_path) if db_path else False
        return self.reader is not None
    
    def close(self):
        """Close the database reader"""
        if self.reader:
            self.reader.close()
            self.reader = None

