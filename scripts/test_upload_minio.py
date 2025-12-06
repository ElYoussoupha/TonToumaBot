import asyncio
import httpx
from uuid import UUID

API_URL = "http://127.0.0.1:9000/api/v1"

# Use the entity ID from the seed script or a hardcoded one
ENTITY_ID = "49438729-cfa0-42fb-af9f-a90e70816d67" 

async def test_upload():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("🚀 Testing MinIO Upload...")

        # Create a dummy file
        file_content = b"This is a test document content for MinIO storage."
        files = {
            "file": ("test_minio.txt", file_content, "text/plain")
        }
        data = {
            "title": "Test MinIO Document",
            "entity_id": ENTITY_ID
        }

        try:
            response = await client.post(f"{API_URL}/kb/documents", data=data, files=files)
            if response.status_code in [200, 201]:
                print("✅ Upload successful!")
                print(response.json())
            else:
                print(f"❌ Upload failed: {response.text}")
        except Exception as e:
            print(f"❌ Exception during upload: {repr(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_upload())
