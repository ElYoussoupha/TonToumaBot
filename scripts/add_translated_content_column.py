"""
Script to add translated_content column to messages table.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

async def add_translated_content_column():
    print("[Migration] Adding translated_content column to messages table...")
    
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'messages' AND column_name = 'translated_content'
        """))
        exists = result.fetchone()
        
        if exists:
            print("[OK] Column 'translated_content' already exists.")
            return
        
        # Add the column
        await conn.execute(text("""
            ALTER TABLE messages 
            ADD COLUMN translated_content TEXT NULL
        """))
        print("[OK] Column 'translated_content' added successfully!")

if __name__ == "__main__":
    asyncio.run(add_translated_content_column())
