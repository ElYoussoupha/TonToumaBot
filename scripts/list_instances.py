import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.entity import Instance

async def list_instances():
    engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    async with engine.connect() as conn:
        result = await conn.execute(select(Instance))
        instances = result.fetchall()
        
        if not instances:
            print("Aucune instance trouvée.")
        else:
            print(f"{'ID':<40} | {'Name':<25} | {'Description':<30}")
            print("-" * 100)
            for inst in instances:
                desc = inst.description if inst.description else "N/A"
                print(f"{str(inst.instance_id):<40} | {inst.name:<25} | {desc:<30}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(list_instances())
