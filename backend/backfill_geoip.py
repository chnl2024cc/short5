#!/usr/bin/env python3
"""
Backfill script to update existing visitor_logs records with GeoIP data
This will re-process IP addresses that don't have geo data yet
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, '/app')

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.services.geoip_service import GeoIPService
from app.models.visitor_log import VisitorLog
from sqlalchemy import select, update
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def backfill_geoip():
    """Backfill GeoIP data for existing visitor logs"""
    logger.info("Starting GeoIP backfill...")
    
    # Initialize GeoIP service
    geoip_service = GeoIPService(db_path=settings.GEOIP_DB_PATH)
    
    if not geoip_service.is_available():
        logger.error("GeoIP service is not available. Cannot backfill.")
        return
    
    logger.info("GeoIP service initialized successfully")
    
    async with AsyncSessionLocal() as db:
        # Find records that need GeoIP data
        # Look for records with IP addresses but missing geo data (or have default Alaska values)
        query = select(VisitorLog).where(
            VisitorLog.ip_address.isnot(None),
            # Either missing country/city, or have default Alaska coordinates
            (
                (VisitorLog.country.is_(None)) |
                (VisitorLog.city == 'Unknown') |
                (VisitorLog.latitude == 61.2181)  # Default Alaska latitude
            )
        )
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        logger.info(f"Found {len(records)} records to process")
        
        updated_count = 0
        error_count = 0
        
        for record in records:
            try:
                ip_address = str(record.ip_address)
                
                # Skip private/localhost IPs
                if ip_address in ('127.0.0.1', '::1', 'localhost') or \
                   ip_address.startswith('192.168.') or \
                   ip_address.startswith('10.') or \
                   ip_address.startswith('172.'):
                    logger.debug(f"Skipping private IP: {ip_address}")
                    continue
                
                # Perform GeoIP lookup
                geo_data = geoip_service.lookup(ip_address)
                
                # Only update if we got real data (not Alaska defaults)
                if geo_data.get('country') and geo_data.get('country') != 'US':
                    # Update record
                    await db.execute(
                        update(VisitorLog)
                        .where(VisitorLog.id == record.id)
                        .values(
                            country=geo_data.get('country'),
                            country_name=geo_data.get('country_name'),
                            city=geo_data.get('city'),
                            latitude=geo_data.get('latitude'),
                            longitude=geo_data.get('longitude'),
                        )
                    )
                    updated_count += 1
                    logger.info(f"Updated record {record.id} for IP {ip_address}: "
                              f"{geo_data.get('country')}, {geo_data.get('city')}")
                elif geo_data.get('country') == 'US' and geo_data.get('city') != 'Unknown':
                    # US IP with real city data (not Alaska default)
                    await db.execute(
                        update(VisitorLog)
                        .where(VisitorLog.id == record.id)
                        .values(
                            country=geo_data.get('country'),
                            country_name=geo_data.get('country_name'),
                            city=geo_data.get('city'),
                            latitude=geo_data.get('latitude'),
                            longitude=geo_data.get('longitude'),
                        )
                    )
                    updated_count += 1
                    logger.info(f"Updated record {record.id} for IP {ip_address}: "
                              f"{geo_data.get('country')}, {geo_data.get('city')}")
                else:
                    logger.debug(f"No geo data for IP {ip_address} (might be private or not in database)")
                
                # Commit every 100 records
                if updated_count % 100 == 0:
                    await db.commit()
                    logger.info(f"Committed {updated_count} updates so far...")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing record {record.id}: {e}")
                continue
        
        # Final commit
        await db.commit()
        geoip_service.close()
        
        logger.info(f"Backfill complete!")
        logger.info(f"  - Updated: {updated_count} records")
        logger.info(f"  - Errors: {error_count} records")
        logger.info(f"  - Total processed: {len(records)} records")

if __name__ == "__main__":
    asyncio.run(backfill_geoip())

