from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite:///./calvin_bot.db"
    
    # Bluesky settings
    BLUESKY_USERNAME: str
    BLUESKY_PASSWORD: str
    BLUESKY_API_URL: str = "https://bsky.social/xrpc/"
    
    # Comic settings
    POSTS_PER_DAY: int = 2
    MIN_HOURS_BETWEEN_POSTS: int = 8
    
    # Application settings
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()