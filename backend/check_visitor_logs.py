#!/usr/bin/env python3
"""
Check what's in the visitor_logs table for a specific IP
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, '/app')

from app.core.database import AsyncSessionLocal
from app.models.visitor_log import VisitorLog
from sqlalchemy import select, cast, String
from sqlalchemy.dialects.postgresql import INET
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_visitor_logs():
    """Check visitor logs"""
    async with AsyncSessionLocal() as db:
        # Get all records with IP addresses
        query = select(VisitorLog).where(
            VisitorLog.ip_address.isnot(None)
        ).order_by(VisitorLog.visited_at.desc()).limit(20)
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        logger.info(f"Found {len(records)} records with IP addresses\n")
        
        # Check for the specific IP
        target_ip = '5.146.192.170'
        found_target = False
        
        for record in records:
            ip_str = str(record.ip_address)
            is_target = target_ip in ip_str
            
            if is_target:
                found_target = True
                print("=" * 70)
                print(f"*** FOUND TARGET IP ***")
                print("=" * 70)
            
            print(f"Record ID: {record.id}")
            print(f"  IP: {ip_str}")
            print(f"  Country: {record.country}")
            print(f"  Country Name: {record.country_name}")
            print(f"  City: {record.city}")
            print(f"  Latitude: {record.latitude}")
            print(f"  Longitude: {record.longitude}")
            print(f"  Visited At: {record.visited_at}")
            print(f"  URL: {record.url}")
            print()
        
        if not found_target:
            print(f"\n⚠️  No records found for IP: {target_ip}")
            print("   Showing recent records above for reference.")

if __name__ == "__main__":
    asyncio.run(check_visitor_logs())

