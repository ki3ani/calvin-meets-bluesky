import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DynamoDB settings (for storing comic records and generated content)
    DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "Comics")
    DYNAMODB_CONTENT_TABLE: str = os.getenv("DYNAMODB_CONTENT_TABLE", "GeneratedContent")

    # AWS settings
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")

    # AWS Bedrock settings
    BEDROCK_REGION: str = os.getenv("BEDROCK_REGION", "us-east-1")
    BEDROCK_CLAUDE_MODEL: str = os.getenv(
        "BEDROCK_CLAUDE_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    BEDROCK_STABILITY_MODEL: str = os.getenv(
        "BEDROCK_STABILITY_MODEL", "stability.stable-diffusion-xl-v1"
    )
    BEDROCK_MAX_TOKENS: int = int(os.getenv("BEDROCK_MAX_TOKENS", "2000"))
    BEDROCK_TEMPERATURE: float = float(os.getenv("BEDROCK_TEMPERATURE", "1.0"))

    # Bluesky settings
    BLUESKY_USERNAME: str = os.getenv("BLUESKY_USERNAME", "")
    BLUESKY_PASSWORD: str = os.getenv("BLUESKY_PASSWORD", "")
    BLUESKY_API_URL: str = "https://bsky.social/xrpc/"

    # Application settings
    USE_S3_STORAGE: bool = True
    MIN_HOURS_BETWEEN_POSTS: int = 8
    DEBUG: bool = False

    # Content generation settings
    CONTENT_TYPES: list = [
        "philosophy",
        "joke",
        "story",
        "poem",
        "wisdom",
    ]
    MIN_QUALITY_SCORE: float = 0.7
    ENABLE_IMAGE_GENERATION: bool = os.getenv("ENABLE_IMAGE_GENERATION", "true").lower() == "true"

    class Config:
        env_file = None  # Don't load .env file in Lambda


@lru_cache()
def get_settings():
    """Cache settings for Lambda's lifetime"""
    return Settings()
