from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PostBase(BaseModel):
    comic_id: int
    post_text: str


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    post_text: Optional[str]
    likes: Optional[int]
    reposts: Optional[int]


class Post(PostBase):
    id: int
    bluesky_post_id: Optional[str]
    posted_at: datetime
    likes: int = 0
    reposts: int = 0
    replies: int = 0

    class Config:
        orm_mode = True


class PostWithEngagement(Post):
    engagement_rate: float
    comic_title: Optional[str]
    comic_date: datetime
