"""
Script to add dashboard_modules column to entities table.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

async def add_dashboard_modules_column():
    print("[Migration] Adding dashboard_modules column to entities table...")
    
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'entities' AND column_name = 'dashboard_modules'
        """))
        exists = result.fetchone()
        
        if exists:
            print("[OK] Column 'dashboard_modules' already exists.")
        else:
            await conn.execute(text("""
                ALTER TABLE entities 
                ADD COLUMN dashboard_modules JSONB DEFAULT '[]'::jsonb
            """))
            print("[OK] Column 'dashboard_modules' added successfully!")
        
        # Update Hopital Fann to have personnel module
        print("[Migration] Setting personnel module for Hôpital Fann...")
        await conn.execute(text("""
            UPDATE entities 
            SET dashboard_modules = '["personnel"]'::jsonb
            WHERE name LIKE '%Hôpital%' OR name LIKE '%Hopital%'
        """))
        print("[OK] Hôpital entities updated with 'personnel' module.")

if __name__ == "__main__":
    asyncio.run(add_dashboard_modules_column())
