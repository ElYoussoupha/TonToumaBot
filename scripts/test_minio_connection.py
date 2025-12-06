from minio import Minio
from minio.error import S3Error
import io

# Configuration matching app/core/config.py
MINIO_ENDPOINT = "127.0.0.1:9100"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "tontouma-knowledge"
MINIO_SECURE = False

def test_minio_direct():
    print(f"Testing connection to {MINIO_ENDPOINT}...")
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        
        # Check if bucket exists
        print(f"Checking bucket '{MINIO_BUCKET}'...")
        if not client.bucket_exists(MINIO_BUCKET):
            print(f"Bucket '{MINIO_BUCKET}' does not exist. Creating...")
            client.make_bucket(MINIO_BUCKET)
        else:
            print(f"Bucket '{MINIO_BUCKET}' exists.")
            
        # Try upload
        print("Attempting upload...")
        file_name = "test_direct_upload.txt"
        data = b"Direct upload test content"
        result = client.put_object(
            MINIO_BUCKET,
            file_name,
            io.BytesIO(data),
            len(data),
            content_type="text/plain"
        )
        print(f"✅ Upload successful: {result.object_name}")
        
    except Exception as e:
        print(f"❌ MinIO Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minio_direct()
