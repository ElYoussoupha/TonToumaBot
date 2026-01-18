"""
Script to add system_prompt column to entities table.
Run this before using the new entity-specific prompts feature.
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

async def add_system_prompt_column():
    print("[Migration] Adding system_prompt column to entities table...")
    
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'entities' AND column_name = 'system_prompt'
        """))
        exists = result.fetchone()
        
        if exists:
            print("[OK] Column 'system_prompt' already exists.")
            return
        
        # Add the column
        await conn.execute(text("""
            ALTER TABLE entities 
            ADD COLUMN system_prompt TEXT NULL
        """))
        print("[OK] Column 'system_prompt' added successfully!")

if __name__ == "__main__":
    asyncio.run(add_system_prompt_column())