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
    Service for IP geolocation lookups using local GeoIP database.
    Supports both MaxMind GeoLite2 and DB-IP databases (both use .mmdb format).
    No external API calls - fully self-contained.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize GeoIP service (lazy loading - database not loaded until first lookup)
        
        Args:
            db_path: Path to GeoIP database file (.mmdb format)
                    Supports both MaxMind GeoLite2-City.mmdb and DB-IP dbip-city-lite-*.mmdb
                    Must be provided via GEOIP_DB_PATH environment variable
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
        
        # Require explicit path via environment variable
        if not db_path:
            logger.warning("GEOIP_DB_PATH not set. Geographic tracking will be disabled.")
            return
        
        if not os.path.exists(db_path):
            logger.error(f"GeoIP database file not found at: {db_path}. Geographic tracking will be disabled.")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Absolute path check: {os.path.abspath(db_path) if db_path else 'N/A'}")
            return
        
        try:
            self.reader = geoip2.database.Reader(db_path)
            logger.info(f"GeoIP database loaded successfully from: {db_path}")
            # Test with a known IP to verify it's working
            try:
                test_response = self.reader.city("8.8.8.8")
                logger.info(f"GeoIP database test lookup successful: {test_response.country.name}")
            except Exception as test_e:
                logger.warning(f"GeoIP database test lookup failed: {test_e}")
        except Exception as e:
            logger.error(f"Could not load GeoIP database from {db_path}: {e}", exc_info=True)
    
    def _is_private_ip(self, ip_address: str) -> bool:
        """Check if IP address is private/localhost"""
        if not ip_address or ip_address in ('0.0.0.0', 'localhost'):
            return True
        
        # Check for localhost
        if ip_address in ('127.0.0.1', '::1', 'localhost'):
            return True
        
        # Check for private IPv4 ranges
        if ip_address.startswith('192.168.') or ip_address.startswith('10.') or ip_address.startswith('172.'):
            return True
        
        # Check for IPv6 localhost/private
        if ip_address.startswith('fe80:') or ip_address.startswith('fc00:') or ip_address.startswith('fd00:'):
            return True
        
        return False
    
    def _get_alaska_default(self) -> Dict:
        """Get default Alaska location for unknown/private IPs"""
        return {
            'country': 'US',
            'country_name': 'United States',
            'city': 'Unknown',
            'latitude': 61.2181,  # Anchorage, Alaska coordinates
            'longitude': -149.9003,
        }
    
    def lookup(self, ip_address: str) -> Dict:
        """
        Lookup geographic information for an IP address
        
        Args:
            ip_address: IP address string (IPv4 or IPv6)
        
        Returns:
            Dict with country, city, coordinates, etc.
            Returns meaningful default values if lookup fails or IP is private.
        """
        # Lazy initialization - only load database when lookup is actually called
        self._ensure_initialized()
        
        # Default result with meaningful values for unknown/private IPs
        result = {
            'country': None,
            'country_name': None,
            'city': None,
            'latitude': None,
            'longitude': None,
        }
        
        # Check if it's a private/localhost IP
        if self._is_private_ip(ip_address):
            alaska_default = self._get_alaska_default()
            logger.debug(f"Private/localhost IP detected: {ip_address} - setting Alaska default location")
            return alaska_default
        
        if not self.reader:
            # Database not available - set Alaska default
            alaska_default = self._get_alaska_default()
            logger.debug(f"GeoIP database not available - setting Alaska default location")
            return alaska_default
        
        try:
            response = self.reader.city(ip_address)
            
            # Extract country data (safe attribute access)
            if hasattr(response, 'country') and response.country:
                result['country'] = getattr(response.country, 'iso_code', None)
                result['country_name'] = getattr(response.country, 'name', None)
            
            # Extract city data (safe attribute access)
            if hasattr(response, 'city') and response.city:
                result['city'] = getattr(response.city, 'name', None)
            
            # Extract coordinates (safe attribute access)
            if hasattr(response, 'location') and response.location:
                lat = getattr(response.location, 'latitude', None)
                lon = getattr(response.location, 'longitude', None)
                if lat is not None and lon is not None:
                    try:
                        result['latitude'] = float(lat)
                        result['longitude'] = float(lon)
                    except (ValueError, TypeError):
                        pass
            
            # Log lookup result
            if result['country'] or result['city']:
                logger.info(f"GeoIP lookup successful for {ip_address}: country={result['country']}, city={result['city']}, coords=({result['latitude']}, {result['longitude']})")
            else:
                # IP found in database but no data available - set Alaska default
                alaska_default = self._get_alaska_default()
                result.update(alaska_default)
                logger.debug(f"GeoIP lookup returned no data for {ip_address} - setting Alaska default location")
                
        except geoip2.errors.AddressNotFoundError:
            # IP not in database - set Alaska default
            alaska_default = self._get_alaska_default()
            result.update(alaska_default)
            logger.debug(f"IP address not found in database: {ip_address} - setting Alaska default location")
        except AttributeError as e:
            # Handle potential differences in DB-IP vs MaxMind response structure
            logger.warning(f"GeoIP response structure issue for {ip_address}: {e}")
            alaska_default = self._get_alaska_default()
            result.update(alaska_default)
            # Try to inspect what we got
            try:
                logger.warning(f"Response type: {type(response)}, has country: {hasattr(response, 'country')}, has city: {hasattr(response, 'city')}")
            except:
                pass
        except Exception as e:
            logger.error(f"GeoIP lookup error for {ip_address}: {e}", exc_info=True)
            alaska_default = self._get_alaska_default()
            result.update(alaska_default)
        
        return result
    
    def is_available(self) -> bool:
        """Check if GeoIP service is available (lazy check - doesn't load database)"""
        if not self._initialized:
            # Check if database file exists without loading it
            db_path = self._db_path
            if not db_path:
                return False
            return os.path.exists(db_path)
        return self.reader is not None
    
    def close(self):
        """Close the database reader"""
        if self.reader:
            self.reader.close()
            self.reader = None

