from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session
from app.services.comic_service import ComicService
from app.services.bluesky_service import BlueskyService
from app.utils.post_formatter import PostFormatter
import random
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, db: Session):
        self.db = db
        self.comic_service = ComicService()
        self.bluesky_service = BlueskyService()
        self.post_formatter = PostFormatter()
        
    async def fetch_new_comics(self, days_back: int = 7):
        """Fetch comics from the last n days"""
        for i in range(days_back):
            date = datetime.now() - timedelta(days=i)
            try:
                comic_data = await self.comic_service.fetch_calvin_and_hobbes(date)
                await self.comic_service.save_comic(self.db, comic_data)
            except Exception as e:
                logger.error(f"Error fetching comic for {date}: {str(e)}")
    
    async def create_post(self):
        """Create a new post with a random unposted comic"""
        try:
            # Get random unposted comic
            comic = await self.comic_service.get_random_unposted_comic(self.db)
            if not comic:
                logger.warning("No unposted comics available")
                return None
                
            # Create post text
            captions = self.post_formatter.create_random_captions()
            post_text = f"{random.choice(captions)}\n\n"
            post_text += self.post_formatter.create_post_text(
                comic.strip_date,
                comic.title
            )
            
            # Create post on Bluesky
            result = await self.bluesky_service.create_post(
                post_text,
                comic.local_path
            )
            
            # Mark comic as posted
            await self.comic_service.mark_as_posted(self.db, comic.id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            return None
    
    async def run_scheduler(self):
        """Run the scheduler"""
        while True:
            try:
                # Fetch new comics periodically
                await self.fetch_new_comics()
                
                # Create a new post
                await self.create_post()
                
                # Wait for next posting time (e.g., 12 hours)
                await asyncio.sleep(43200)  # 12 hours
                
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
