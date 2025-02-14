from pydantic import BaseSettings

class TestSettings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite:///./test.db"

    # Test Bluesky settings
    BLUESKY_USERNAME: str = "test_user"
    BLUESKY_PASSWORD: str = "test_password"
    BLUESKY_API_URL: str = "https://test.bsky.social/xrpc/"

    # Comic settings
    POSTS_PER_DAY: int = 2
    MIN_HOURS_BETWEEN_POSTS: int = 8

    # Application settings
    DEBUG: bool = True