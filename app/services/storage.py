from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import io

class MinioService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload_file(self, file_data: bytes, file_name: str, content_type: str) -> str:
        """
        Uploads a file to MinIO and returns the object name.
        """
        try:
            result = self.client.put_object(
                self.bucket_name,
                file_name,
                io.BytesIO(file_data),
                len(file_data),
                content_type=content_type
            )
            return file_name
        except S3Error as e:
            print(f"MinIO Upload Error: {e}")
            raise e

    def get_file_url(self, file_name: str) -> str:
        """
        Generates a presigned URL for the file.
        """
        return self.client.presigned_get_object(self.bucket_name, file_name)

    def delete_file(self, file_name: str):
        self.client.remove_object(self.bucket_name, file_name)

storage_service = MinioService()
