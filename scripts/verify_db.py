import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def verify_db():
    print(f"Connecting to {settings.SQLALCHEMY_DATABASE_URI}")
    engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"✅ Database connection successful: {result.scalar()}")
            
            # Check if tables exist
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = result.fetchall()
            print(f"Tables found: {[t[0] for t in tables]}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_db())
