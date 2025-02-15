import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DynamoDB settings (for storing comic records)
    DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "Comics")

    # AWS settings
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")

    # Bluesky settings
    BLUESKY_USERNAME: str = os.getenv("BLUESKY_USERNAME", "")
    BLUESKY_PASSWORD: str = os.getenv("BLUESKY_PASSWORD", "")
    BLUESKY_API_URL: str = "https://bsky.social/xrpc/"

    # Application settings
    USE_S3_STORAGE: bool = True
    MIN_HOURS_BETWEEN_POSTS: int = 8
    DEBUG: bool = False

    class Config:
        env_file = None  # Don't load .env file in Lambda


@lru_cache()
def get_settings():
    """Cache settings for Lambda's lifetime"""
    return Settings()
