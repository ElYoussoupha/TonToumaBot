"""
Script to add 'App Mobile' instance for each entity.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

async def add_mobile_instances():
    print("[Migration] Adding App Mobile instances for all entities...")
    
    async with engine.begin() as conn:
        # Get all entities
        result = await conn.execute(text("""
            SELECT entity_id, name FROM entities
        """))
        entities = result.fetchall()
        
        for entity_id, entity_name in entities:
            instance_name = f"App Mobile {entity_name}"
            
            # Check if already exists
            check = await conn.execute(text("""
                SELECT instance_id FROM instances 
                WHERE entity_id = :entity_id AND name = :name
            """), {"entity_id": entity_id, "name": instance_name})
            
            if check.fetchone():
                print(f"  [Skip] Instance already exists: {instance_name}")
                continue
            
            # Generate API key
            import uuid
            api_key = f"mob_{uuid.uuid4().hex[:16]}"
            
            # Insert instance
            await conn.execute(text("""
                INSERT INTO instances (instance_id, entity_id, name, description, api_key)
                VALUES (gen_random_uuid(), :entity_id, :name, :description, :api_key)
            """), {
                "entity_id": entity_id,
                "name": instance_name,
                "description": f"Instance mobile pour {entity_name}",
                "api_key": api_key
            })
            print(f"  [OK] Created: {instance_name}")
        
        print("[Done] Mobile instances added.")

if __name__ == "__main__":
    asyncio.run(add_mobile_instances())
