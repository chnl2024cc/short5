#!/usr/bin/env python3
"""
Test script to check a specific IP address - can be run in Docker
Usage: docker exec short5_backend python test_ip_docker.py
"""
import os
import sys
import logging

# Add app to path
sys.path.insert(0, '/app')

from app.core.config import settings
from app.services.geoip_service import GeoIPService
import geoip2.database
import geoip2.errors

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ip(ip_address: str):
    """Test a specific IP address"""
    print(f"\n{'='*70}")
    print(f"Testing IP: {ip_address}")
    print(f"{'='*70}\n")
    
    db_path = settings.GEOIP_DB_PATH
    print(f"GEOIP_DB_PATH: {db_path}")
    print(f"File exists: {os.path.exists(db_path) if db_path else False}\n")
    
    if not db_path or not os.path.exists(db_path):
        print("ERROR: GeoIP database not found!")
        return
    
    # Test 1: Direct database lookup
    print("=" * 70)
    print("TEST 1: Direct database lookup (raw geoip2)")
    print("=" * 70)
    try:
        reader = geoip2.database.Reader(db_path)
        print("✓ Database loaded successfully\n")
        
        try:
            response = reader.city(ip_address)
            print(f"✓ IP found in database!\n")
            
            # Inspect response
            print("Response inspection:")
            print(f"  Type: {type(response)}")
            print(f"  Has 'country': {hasattr(response, 'country')}")
            print(f"  Has 'city': {hasattr(response, 'city')}")
            print(f"  Has 'location': {hasattr(response, 'location')}\n")
            
            # Check country
            if hasattr(response, 'country'):
                country = response.country
                print(f"Country object:")
                print(f"  Value: {country}")
                print(f"  Type: {type(country) if country else 'None'}")
                if country:
                    print(f"  Attributes: {[a for a in dir(country) if not a.startswith('_')]}")
                    if hasattr(country, 'iso_code'):
                        print(f"  iso_code: {getattr(country, 'iso_code', 'N/A')}")
                    if hasattr(country, 'code'):
                        print(f"  code: {getattr(country, 'code', 'N/A')}")
                    if hasattr(country, 'name'):
                        print(f"  name: {getattr(country, 'name', 'N/A')}")
                    if hasattr(country, 'names'):
                        names = getattr(country, 'names', None)
                        print(f"  names: {names}")
            
            # Check city
            if hasattr(response, 'city'):
                city = response.city
                print(f"\nCity object:")
                print(f"  Value: {city}")
                print(f"  Type: {type(city) if city else 'None'}")
                if city:
                    print(f"  Attributes: {[a for a in dir(city) if not a.startswith('_')]}")
                    if hasattr(city, 'name'):
                        print(f"  name: {getattr(city, 'name', 'N/A')}")
                    if hasattr(city, 'names'):
                        names = getattr(city, 'names', None)
                        print(f"  names: {names}")
            
            # Check location
            if hasattr(response, 'location'):
                location = response.location
                print(f"\nLocation object:")
                print(f"  Value: {location}")
                print(f"  Type: {type(location) if location else 'None'}")
                if location:
                    print(f"  Attributes: {[a for a in dir(location) if not a.startswith('_')]}")
                    if hasattr(location, 'latitude'):
                        print(f"  latitude: {getattr(location, 'latitude', 'N/A')}")
                    if hasattr(location, 'longitude'):
                        print(f"  longitude: {getattr(location, 'longitude', 'N/A')}")
            
        except geoip2.errors.AddressNotFoundError:
            print(f"\n✗ IP address NOT FOUND in database")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            reader.close()
    
    except Exception as e:
        print(f"ERROR loading database: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Using GeoIPService
    print("\n" + "=" * 70)
    print("TEST 2: Using GeoIPService (our service)")
    print("=" * 70)
    try:
        geoip_service = GeoIPService(db_path=db_path)
        result = geoip_service.lookup(ip_address)
        
        print(f"\nGeoIPService result:")
        print(f"  country: {result.get('country')}")
        print(f"  country_name: {result.get('country_name')}")
        print(f"  city: {result.get('city')}")
        print(f"  latitude: {result.get('latitude')}")
        print(f"  longitude: {result.get('longitude')}")
        
        geoip_service.close()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ip("5.146.192.170")
    
    print("\n" + "=" * 70)
    print("COMPARISON: Testing known working IP (8.8.8.8)")
    print("=" * 70)
    test_ip("8.8.8.8")

