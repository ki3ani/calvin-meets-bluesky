from datetime import datetime, timedelta
from app.database.models import Comic
from sqlalchemy.orm import Session
import asyncio
import random
import requests
from bs4 import BeautifulSoup
import os
import logging

logger = logging.getLogger(__name__)

class ComicService:
    def __init__(self):
        self.comic_dir = "comic_images"
        self.base_url = "https://www.gocomics.com/calvinandhobbes"
        
    def _ensure_comic_dir(self):
        """Ensure the comic images directory exists"""
        if not os.path.exists(self.comic_dir):
            os.makedirs(self.comic_dir)
    
    async def fetch_calvin_and_hobbes(self, date: datetime = None):
        """Fetch Calvin and Hobbes comic for a specific date"""
        try:
            if not date:
                date = datetime.now()
            
            # Format date as YYYY/MM/DD
            formatted_date = date.strftime('%Y/%m/%d')
            url = f"{self.base_url}/{formatted_date}"
            
            logger.info(f"Fetching comic from URL: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the comic image
            comic_image = soup.find('picture', class_='item-comic-image')
            if not comic_image:
                comic_image = soup.select_one('.comic__image img')
            
            if comic_image:
                # If it's a picture tag, get the img inside
                img_tag = comic_image.find('img') if comic_image.name == 'picture' else comic_image
                image_url = img_tag.get('src', '') or img_tag.get('data-src', '')
                
                if not image_url:
                    raise Exception("No image URL found")
                
                return {
                    "date": date,
                    "image_url": image_url,
                    "title": f"Calvin and Hobbes - {date.strftime('%Y-%m-%d')}",
                    "local_path": None
                }
            raise Exception("Could not find comic image")
            
        except Exception as e:
            logger.error(f"Error fetching comic for {date}: {str(e)}")
            raise

    async def download_image(self, image_url: str, comic_date: datetime):
        """Download and save comic image"""
        try:
            self._ensure_comic_dir()
            file_name = f"calvin_{comic_date.strftime('%Y%m%d')}.png"
            file_path = os.path.join(self.comic_dir, file_name)
            
            if not os.path.exists(file_path):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(image_url, headers=headers)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Downloaded image to {file_path}")
            
            return file_path
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            raise

    async def get_random_unposted_comic(self, db: Session):
        """Get a random unposted comic from the database"""
        try:
            unposted_comics = db.query(Comic).filter(Comic.posted == False).all()
            if not unposted_comics:
                logger.info("No unposted comics available")
                return None
            return random.choice(unposted_comics)
        except Exception as e:
            logger.error(f"Error getting random unposted comic: {str(e)}")
            raise
    
    async def save_comic(self, db: Session, comic_data: dict):
        """Save comic to database"""
        try:
            # Check if comic already exists
            existing_comic = db.query(Comic).filter(
                Comic.strip_date == comic_data["date"]
            ).first()
            
            if existing_comic:
                logger.info(f"Comic for {comic_data['date']} already exists")
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
            try:
                db.commit()
                db.refresh(db_comic)
                logger.info(f"Successfully saved comic for {comic_data['date']}")
                return db_comic
            except Exception as e:
                db.rollback()
                logger.error(f"Error saving comic: {str(e)}")
                raise
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error in save_comic: {str(e)}")
            raise
    
    async def mark_as_posted(self, db: Session, comic_id: int):
        """Mark a comic as posted"""
        try:
            comic = db.query(Comic).filter(Comic.id == comic_id).first()
            if comic:
                comic.posted = True
                db.commit()
                logger.info(f"Marked comic {comic_id} as posted")
                return comic
            logger.warning(f"Comic {comic_id} not found")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking comic as posted: {str(e)}")
            raise