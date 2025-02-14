from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ComicBase(BaseModel):
    strip_date: datetime
    url: str
    title: Optional[str] = None


class ComicCreate(ComicBase):
    pass


class Comic(ComicBase):
    id: int
    local_path: Optional[str]
    posted: bool
    created_at: datetime

    class Config:
        orm_mode = True
