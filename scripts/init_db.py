import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.base import Base
from app.models import * # Import all models

async def init_db():
    engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    async with engine.begin() as conn:
        # Create pgvector extension if not exists
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    print("✅ Database schema initialized successfully.")
    await engine.dispose()

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(init_db())
