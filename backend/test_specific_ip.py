#!/usr/bin/env python3
"""
Test script to check a specific IP address in the GeoIP database
"""
import os
import sys
import logging

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.services.geoip_service import GeoIPService
import geoip2.database
import geoip2.errors

# Configure logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_specific_ip(ip_address: str):
    """Test a specific IP address"""
    print(f"\n{'='*60}")
    print(f"Testing IP: {ip_address}")
    print(f"{'='*60}\n")
    
    db_path = settings.GEOIP_DB_PATH
    print(f"GEOIP_DB_PATH: {db_path}")
    print(f"File exists: {os.path.exists(db_path) if db_path else False}\n")
    
    if not db_path:
        print("ERROR: GEOIP_DB_PATH is not set!")
        return
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at: {db_path}")
        return
    
    # Test 1: Direct database lookup
    print("=" * 60)
    print("TEST 1: Direct database lookup (raw)")
    print("=" * 60)
    try:
        reader = geoip2.database.Reader(db_path)
        print("✓ Database loaded successfully")
        
        try:
            response = reader.city(ip_address)
            print(f"\n✓ IP found in database!")
            print(f"\nResponse object type: {type(response)}")
            print(f"Response attributes: {dir(response)}")
            
            # Check country
            if hasattr(response, 'country'):
                country = response.country
                print(f"\nCountry object: {country}")
                if country:
                    print(f"  - hasattr(country, 'iso_code'): {hasattr(country, 'iso_code')}")
                    print(f"  - hasattr(country, 'name'): {hasattr(country, 'name')}")
                    if hasattr(country, 'iso_code'):
                        print(f"  - iso_code: {getattr(country, 'iso_code', 'N/A')}")
                    if hasattr(country, 'name'):
                        print(f"  - name: {getattr(country, 'name', 'N/A')}")
                else:
                    print("  - Country is None/empty")
            else:
                print("\n✗ No 'country' attribute in response")
            
            # Check city
            if hasattr(response, 'city'):
                city = response.city
                print(f"\nCity object: {city}")
                if city:
                    print(f"  - hasattr(city, 'name'): {hasattr(city, 'name')}")
                    if hasattr(city, 'name'):
                        print(f"  - name: {getattr(city, 'name', 'N/A')}")
                else:
                    print("  - City is None/empty")
            else:
                print("\n✗ No 'city' attribute in response")
            
            # Check location
            if hasattr(response, 'location'):
                location = response.location
                print(f"\nLocation object: {location}")
                if location:
                    print(f"  - hasattr(location, 'latitude'): {hasattr(location, 'latitude')}")
                    print(f"  - hasattr(location, 'longitude'): {hasattr(location, 'longitude')}")
                    if hasattr(location, 'latitude'):
                        print(f"  - latitude: {getattr(location, 'latitude', 'N/A')}")
                    if hasattr(location, 'longitude'):
                        print(f"  - longitude: {getattr(location, 'longitude', 'N/A')}")
                else:
                    print("  - Location is None/empty")
            else:
                print("\n✗ No 'location' attribute in response")
            
            # Try to access all attributes
            print(f"\nAll response attributes:")
            for attr in dir(response):
                if not attr.startswith('_'):
                    try:
                        value = getattr(response, attr)
                        if not callable(value):
                            print(f"  - {attr}: {value}")
                    except:
                        pass
            
        except geoip2.errors.AddressNotFoundError:
            print(f"\n✗ IP address NOT FOUND in database")
        except AttributeError as e:
            print(f"\n✗ AttributeError: {e}")
            print(f"  This might indicate a database format issue")
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
    print("\n" + "=" * 60)
    print("TEST 2: Using GeoIPService (our service)")
    print("=" * 60)
    try:
        geoip_service = GeoIPService(db_path=db_path)
        result = geoip_service.lookup(ip_address)
        
        print(f"\nGeoIPService result:")
        print(f"  - country: {result.get('country')}")
        print(f"  - country_name: {result.get('country_name')}")
        print(f"  - city: {result.get('city')}")
        print(f"  - latitude: {result.get('latitude')}")
        print(f"  - longitude: {result.get('longitude')}")
        
        geoip_service.close()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ip = "5.146.192.170"
    test_specific_ip(test_ip)
    
    # Also test a known working IP for comparison
    print("\n" + "=" * 60)
    print("COMPARISON: Testing known working IP (8.8.8.8)")
    print("=" * 60)
    test_specific_ip("8.8.8.8")

