import asyncio
import logging

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import models
from app.database.session import engine, get_db
from app.services.bluesky_service import BlueskyService
from app.services.comic_service import ComicService
from app.services.scheduler_service import SchedulerService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Calvin and Hobbes Bot")

# Initialize services
comic_service = ComicService()
bluesky_service = BlueskyService()


@app.on_event("startup")
async def startup_event():
    """Start the scheduler on startup"""
    try:
        # Create database tables if they don't exist
        models.Base.metadata.create_all(bind=engine)

        # Initialize scheduler
        db = next(get_db())
        scheduler = SchedulerService(db)
        asyncio.create_task(scheduler.run_scheduler())
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")


@app.get("/")
async def read_root():
    return {"message": "Calvin and Hobbes Bluesky Bot", "status": "running"}


@app.post("/fetch-comics")
async def fetch_comics(days: int = 7, db: Session = Depends(get_db)):
    """Manually trigger comic fetching"""
    try:
        scheduler = SchedulerService(db)
        await scheduler.fetch_new_comics(days)
        return {"message": f"Fetched comics for the last {days} days"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-post")
async def create_post(db: Session = Depends(get_db)):
    """Manually trigger post creation"""
    try:
        scheduler = SchedulerService(db)
        result = await scheduler.create_post()
        if result:
            return {"message": "Post created successfully", "data": result}
        return {"message": "No comics available for posting"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Get bot status"""
    try:
        total_comics = db.query(models.Comic).count()
        posted_comics = (
            db.query(models.Comic).filter(models.Comic.posted == True).count() # noqa
        )
        return {
            "total_comics": total_comics,
            "posted_comics": posted_comics,
            "unposted_comics": total_comics - posted_comics,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
