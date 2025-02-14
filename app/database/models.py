from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Comic(Base):
    __tablename__ = "comics"

    id = Column(Integer, primary_key=True, index=True)
    strip_date = Column(DateTime, nullable=False)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    local_path = Column(String)
    posted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="comic")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    comic_id = Column(Integer, ForeignKey("comics.id"))
    post_text = Column(String)
    bluesky_post_id = Column(String, unique=True)
    posted_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)
    reposts = Column(Integer, default=0)
    replies = Column(Integer, default=0)

    comic = relationship("Comic", back_populates="posts")
