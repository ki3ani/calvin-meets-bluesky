from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EngagementBase(BaseModel):
    post_id: int
    likes: int = 0
    reposts: int = 0
    replies: int = 0


class EngagementCreate(EngagementBase):
    pass


class Engagement(EngagementBase):
    id: int
    recorded_at: datetime

    class Config:
        orm_mode = True


class Analytics(BaseModel):
    total_posts: int
    total_likes: int
    total_reposts: int
    total_replies: int
    average_engagement: float
    most_popular_post_id: Optional[int]
    last_post_date: Optional[datetime]

    class Config:
        orm_mode = True
