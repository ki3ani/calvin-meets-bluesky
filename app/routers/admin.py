import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database.session import get_db
from app.services.bluesky_service import BlueskyService
from app.services.scheduler_service import SchedulerService
from app.models.analytics import Analytics
from app.models.post import Post
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

async def test_bluesky_connection() -> bool:
    """Test connection to Bluesky API"""
    try:
        bluesky_service = BlueskyService()
        await bluesky_service.login()
        return True
    except Exception as e:
        logger.error(f"Bluesky connection test failed: {str(e)}")
        return False


@router.get("/statistics", response_model=Analytics)
async def get_statistics(db: Session = Depends(get_db)):
    """Get overall statistics"""
    try:
        # Get post statistics
        total_posts = db.query(func.count(Post.id)).scalar()
        total_likes = db.query(func.sum(Post.likes)).scalar() or 0
        total_reposts = db.query(func.sum(Post.reposts)).scalar() or 0
        total_replies = db.query(func.sum(Post.replies)).scalar() or 0
        
        # Calculate average engagement
        if total_posts > 0:
            average_engagement = (total_likes + total_reposts + total_replies) / total_posts
        else:
            average_engagement = 0.0
            
        # Get most popular post
        most_popular_post = db.query(Post)\
            .order_by((Post.likes + Post.reposts + Post.replies).desc())\
            .first()
            
        # Get last post date
        last_post = db.query(Post)\
            .order_by(Post.posted_at.desc())\
            .first()
            
        return Analytics(
            total_posts=total_posts,
            total_likes=total_likes,
            total_reposts=total_reposts,
            total_replies=total_replies,
            average_engagement=average_engagement,
            most_popular_post_id=most_popular_post.id if most_popular_post else None,
            last_post_date=last_post.posted_at if last_post else None
        )
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-comics")
async def trigger_comic_fetch(days: int = 7, db: Session = Depends(get_db)):
    """Manually trigger comic fetching"""
    try:
        scheduler = SchedulerService(db)
        await scheduler.fetch_new_comics(days)
        return {"message": f"Fetched comics for the last {days} days"}
    except Exception as e:
        logger.error(f"Error fetching comics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-post")
async def trigger_post_creation(db: Session = Depends(get_db)):
    """Manually trigger post creation"""
    try:
        scheduler = SchedulerService(db)
        result = await scheduler.create_post()
        return {"message": "Post created", "data": result}
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-status")
async def get_system_status(db: Session = Depends(get_db)):
    """Get system status information"""
    try:
        return {
            "database_connection": "healthy",
            "image_storage": os.path.exists("comic_images"),
            "bluesky_connection": await test_bluesky_connection(),
            "last_error": None
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
