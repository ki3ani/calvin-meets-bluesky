import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.post import Post, PostUpdate, PostWithEngagement

router = APIRouter(prefix="/posts", tags=["posts"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Post])
async def get_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of posts"""
    try:
        return db.query(Post).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting posts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{post_id}", response_model=PostWithEngagement)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get specific post with engagement data"""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        return PostWithEngagement.from_orm(post)
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{post_id}", response_model=Post)
async def update_post(
    post_id: int, post_update: PostUpdate, db: Session = Depends(get_db)
):
    """Update post information"""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")

        for key, value in post_update.dict(exclude_unset=True).items():
            setattr(post, key, value)

        db.commit()
        db.refresh(post)
        return post
    except Exception as e:
        logger.error(f"Error updating post {post_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete a post"""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")

        db.delete(post)
        db.commit()
        return {"message": "Post deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
