import asyncio
import httpx
import os
import json

# Allow overriding the API URL via environment variable
API_URL = os.environ.get("API_URL", "http://localhost:9000/api/v1")

async def list_entities():
    print(f"Connecting to {API_URL}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/entities")
            if response.status_code == 200:
                entities = response.json()
                print(f"\n[OK] Found {len(entities)} entities:\n")
                print("=" * 60)
                for ent in entities:
                    print(f"ID          : {ent['entity_id']}")
                    print(f"Name        : {ent['name']}")
                    print(f"Description : {ent.get('description', 'N/A')[:100]}...")
                    print(f"Contact     : {ent.get('contact_email', 'N/A')}")
                    print("=" * 60)
            else:
                print(f"[Error] {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[Error] Connection error: {e}")
            print("Is the backend server running on port 9000?")

if __name__ == "__main__":
    asyncio.run(list_entities())
