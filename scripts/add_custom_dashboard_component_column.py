"""
Script to add custom_dashboard_component column to entities table.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

async def add_custom_dashboard_component_column():
    print("[Migration] Adding custom_dashboard_component column to entities table...")
    
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'entities' AND column_name = 'custom_dashboard_component'
        """))
        exists = result.fetchone()
        
        if exists:
            print("[OK] Column 'custom_dashboard_component' already exists.")
            return
        
        # Add the column
        await conn.execute(text("""
            ALTER TABLE entities 
            ADD COLUMN custom_dashboard_component TEXT NULL
        """))
        print("[OK] Column 'custom_dashboard_component' added successfully!")

if __name__ == "__main__":
    asyncio.run(add_custom_dashboard_component_column())
