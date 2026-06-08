from pydantic_settings import BaseSettings
from pathlib import Path

# Go up one level from backend/ to find .env at root
ENV_PATH = Path(__file__).resolve().parents[3] / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:3000"
    GEMINI_API_KEY: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = ""
    AWS_REGION: str = "ap-south-1"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"

    model_config = {"env_file": str(ENV_PATH), "extra": "ignore"}

settings = Settings()