from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = Field(default="sqlite:///./calvin_bot.db")

    # Bluesky settings
    BLUESKY_USERNAME: str
    BLUESKY_PASSWORD: str
    BLUESKY_API_URL: str = Field(default="https://bsky.social/xrpc/")

    # Comic settings
    POSTS_PER_DAY: int = Field(default=2)
    MIN_HOURS_BETWEEN_POSTS: int = Field(default=8)

    # S3 settings
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = Field(default="us-east-1")  # Updated default region
    S3_BUCKET_NAME: str
    USE_S3_STORAGE: bool = Field(default=False)

    # Application settings
    DEBUG: bool = Field(default=False)

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
