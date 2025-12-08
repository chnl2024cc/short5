#!/usr/bin/env python3
"""
Quick test script to verify GeoIP database is working
Run from backend directory: python test_geoip.py
"""
import os
import sys
import geoip2.database
import geoip2.errors

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings

def test_geoip():
    db_path = settings.GEOIP_DB_PATH
    
    print(f"GEOIP_DB_PATH from config: {db_path}")
    print(f"File exists: {os.path.exists(db_path) if db_path else False}")
    
    if not db_path:
        print("ERROR: GEOIP_DB_PATH is not set!")
        return
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at: {db_path}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Absolute path: {os.path.abspath(db_path)}")
        return
    
    try:
        print(f"\nLoading database from: {db_path}")
        reader = geoip2.database.Reader(db_path)
        print("✓ Database loaded successfully!")
        
        # Test with a known public IP
        test_ips = [
            "8.8.8.8",  # Google DNS
            "1.1.1.1",  # Cloudflare DNS
            "208.67.222.222",  # OpenDNS
        ]
        
        print("\nTesting lookups:")
        for ip in test_ips:
            try:
                response = reader.city(ip)
                print(f"\nIP: {ip}")
                print(f"  Country: {response.country.iso_code} - {response.country.name}")
                print(f"  City: {response.city.name if response.city.name else 'N/A'}")
                if response.location:
                    print(f"  Coordinates: {response.location.latitude}, {response.location.longitude}")
                else:
                    print(f"  Coordinates: N/A")
            except geoip2.errors.AddressNotFoundError:
                print(f"\nIP: {ip} - Not found in database")
            except Exception as e:
                print(f"\nIP: {ip} - Error: {e}")
        
        reader.close()
        print("\n✓ All tests completed!")
        
    except Exception as e:
        print(f"ERROR loading database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_geoip()

