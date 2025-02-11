from comics import GoComics
from datetime import datetime, timedelta
from app.database.models import Comic
from sqlalchemy.orm import Session
import asyncio
import random
import requests
import os

class ComicService:
    def __init__(self):
        self.client = GoComics()
        self.comic_dir = "comic_images"
        
    def _ensure_comic_dir(self):
        """Ensure the comic images directory exists"""
        if not os.path.exists(self.comic_dir):
            os.makedirs(self.comic_dir)
    
    async def fetch_calvin_and_hobbes(self, date: datetime = None):
        """Fetch Calvin and Hobbes comic for a specific date"""
        try:
            comic = self.client.get_comic("calvinandhobbes", date)
            return {
                "date": comic.date,
                "image_url": comic.image_url,
                "title": f"Calvin and Hobbes - {comic.date.strftime('%Y-%m-%d')}",
                "local_path": None
            }
        except Exception as e:
            raise Exception(f"Error fetching comic: {str(e)}")
    
    async def download_image(self, image_url: str, comic_date: datetime):
        """Download and save comic image"""
        self._ensure_comic_dir()
        file_name = f"calvin_{comic_date.strftime('%Y%m%d')}.png"
        file_path = os.path.join(self.comic_dir, file_name)
        
        if not os.path.exists(file_path):
            response = requests.get(image_url)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
        
        return file_path
    
    async def get_random_unposted_comic(self, db: Session):
        """Get a random unposted comic from the database"""
        unposted_comics = db.query(Comic).filter(Comic.posted == False).all()
        if not unposted_comics:
            return None
        return random.choice(unposted_comics)
    
    async def save_comic(self, db: Session, comic_data: dict):
        """Save comic to database"""
        # Check if comic already exists
        existing_comic = db.query(Comic).filter(
            Comic.strip_date == comic_data["date"]
        ).first()
        
        if existing_comic:
            return existing_comic
        
        # Download the image
        local_path = await self.download_image(
            comic_data["image_url"], 
            comic_data["date"]
        )
        
        # Create new comic entry
        db_comic = Comic(
            strip_date=comic_data["date"],
            url=comic_data["image_url"],
            title=comic_data["title"],
            local_path=local_path,
            posted=False
        )
        
        db.add(db_comic)
        db.commit()
        db.refresh(db_comic)
        return db_comic
    
    async def mark_as_posted(self, db: Session, comic_id: int):
        """Mark a comic as posted"""
        comic = db.query(Comic).filter(Comic.id == comic_id).first()
        if comic:
            comic.posted = True
            db.commit()
            return comic
        return None
