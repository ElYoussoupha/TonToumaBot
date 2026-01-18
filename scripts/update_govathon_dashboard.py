"""
Script to update GOVATHON 2025 entity with custom_dashboard_component.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

async def update_govathon_dashboard():
    print("[Migration] Updating GOVATHON 2025 entity...")
    
    async with engine.begin() as conn:
        # First ensure the column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'entities' AND column_name = 'custom_dashboard_component'
        """))
        exists = result.fetchone()
        
        if not exists:
            print("[Migration] Adding custom_dashboard_component column...")
            await conn.execute(text("""
                ALTER TABLE entities 
                ADD COLUMN custom_dashboard_component TEXT NULL
            """))
            print("[OK] Column added.")
        
        # Update GOVATHON entity
        result = await conn.execute(text("""
            UPDATE entities 
            SET custom_dashboard_component = 'govathon'
            WHERE name LIKE '%GOVATHON%' OR name LIKE '%Gov''athon%'
            RETURNING name
        """))
        updated = result.fetchall()
        
        if updated:
            for row in updated:
                print(f"[OK] Updated entity: {row[0]}")
        else:
            print("[Warn] No GOVATHON entity found to update.")

if __name__ == "__main__":
    asyncio.run(update_govathon_dashboard())
