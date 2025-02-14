import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.comic import Comic

router = APIRouter(prefix="/comics", tags=["comics"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Comic])
async def get_comics(
    skip: int = 0,
    limit: int = 100,
    posted: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Get list of comics"""
    try:
        query = db.query(Comic)
        if posted is not None:
            query = query.filter(Comic.posted == posted)
        return query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting comics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{comic_id}", response_model=Comic)
async def get_comic(comic_id: int, db: Session = Depends(get_db)):
    """Get specific comic by ID"""
    try:
        comic = db.query(Comic).filter(Comic.id == comic_id).first()
        if comic is None:
            raise HTTPException(status_code=404, detail="Comic not found")
        return comic
    except Exception as e:
        logger.error(f"Error getting comic {comic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/date/{date}")
async def get_comic_by_date(date: str, db: Session = Depends(get_db)):
    """Get comic by date (YYYY-MM-DD)"""
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        comic = db.query(Comic).filter(Comic.strip_date == date_obj).first()
        if comic is None:
            raise HTTPException(status_code=404, detail="Comic not found")
        return comic
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        logger.error(f"Error getting comic for date {date}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
