import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

async def fix_schema():
    print(f"Connecting to {settings.SQLALCHEMY_DATABASE_URI}")
    engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    async with engine.connect() as conn:
        print("Checking for missing columns in 'messages' table...")
        
        # Check if translated_content exists using information_schema
        check_query = text("""
            SELECT count(*) 
            FROM information_schema.columns 
            WHERE table_name='messages' and column_name='translated_content';
        """)
        
        result = await conn.execute(check_query)
        exists = result.scalar() > 0
        
        if exists:
            print("translated_content already exists.")
        else:
            print("translated_content missing. Adding it...")
            await conn.execute(text("ALTER TABLE messages ADD COLUMN translated_content TEXT"))
            await conn.commit()
            print("translated_content added successfully.")
            
    await engine.dispose()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
