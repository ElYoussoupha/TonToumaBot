from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, computed_field
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tontouma Voice Chatbot"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "tontouma"
    POSTGRES_PORT: int = 5432

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TIMEOUT: float = 60.0 # Increased timeout for slow networks
    OPENAI_MAX_RETRIES: int = 3
    UPLOAD_DIR: str = "uploads"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9100" # External access
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "tontouma-knowledge"
    MINIO_SECURE: bool = False

    # LAfricaMobile API
    LAFRICAMOBILE_USERNAME: Optional[str] = None
    LAFRICAMOBILE_PASSWORD: Optional[str] = None
    LAFRICAMOBILE_BASE_URL: str = "https://ttsapi.lafricamobile.com"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    class Config:
        env_file = ".env"

settings = Settings()
