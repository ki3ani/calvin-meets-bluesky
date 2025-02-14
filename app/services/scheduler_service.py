import asyncio
import logging
import random
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.services.bluesky_service import BlueskyService
from app.services.comic_service import ComicService
from app.utils.post_formatter import PostFormatter

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, db: Session):
        self.db = db
        self.comic_service = ComicService()
        self.bluesky_service = BlueskyService()
        self.post_formatter = PostFormatter()

        # Calvin and Hobbes publication dates
        self.start_date = date(1985, 11, 18)  # First strip published
        self.end_date = date(1995, 12, 31)  # Last strip published

        # Scheduler settings
        self.DAYS_BETWEEN_POSTS = 7  # Post every 7 days
        self.COMICS_TO_FETCH = 10  # Fetch 10 comics each time to maintain a buffer

    def get_random_dates(self, count: int = 7):
        """Get random dates from Calvin and Hobbes publication period"""
        dates = []
        total_days = (self.end_date - self.start_date).days

        for _ in range(count):
            random_days = random.randint(0, total_days)  # nosec
            random_date = self.start_date + timedelta(days=random_days)
            dates.append(random_date)

        return sorted(dates)  # Return dates in chronological order

    async def fetch_new_comics(self, days: int = 7):
        """Fetch comics from random dates in the publication period"""
        random_dates = self.get_random_dates(days)

        for fetch_date in random_dates:
            try:
                # Convert date to datetime
                fetch_datetime = datetime.combine(fetch_date, datetime.min.time())
                logger.info(f"Attempting to fetch comic for {fetch_date}")

                comic_data = await self.comic_service.fetch_calvin_and_hobbes(
                    fetch_datetime
                )
                if comic_data:
                    await self.comic_service.save_comic(self.db, comic_data)
                    await asyncio.sleep(2)  # Small delay between requests

            except Exception as e:
                logger.error(f"Error fetching comic for {fetch_date}: {str(e)}")
                continue

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
            post_text = f"{random.choice(captions)}\n\n"  # nosec
            post_text += self.post_formatter.create_post_text(
                comic.strip_date, comic.title
            )

            logger.info(f"Creating post with comic from {comic.strip_date}")

            try:
                # Create post on Bluesky
                result = await self.bluesky_service.create_post(
                    post_text, comic.local_path
                )

                if result:
                    # Mark comic as posted
                    await self.comic_service.mark_as_posted(self.db, comic.id)
                    logger.info(f"Successfully posted comic from {comic.strip_date}")
                    return result
                else:
                    logger.error("Bluesky post creation returned None")
                    return None

            except Exception as e:
                logger.error(f"Error creating Bluesky post: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error in create_post: {str(e)}")
            return None

    async def run_scheduler(self):
        """Run the scheduler"""
        while True:
            try:
                # Log scheduler run
                logger.info(f"Scheduler running at {datetime.now()}")

                # Fetch new comics to maintain buffer
                await self.fetch_new_comics(days=self.COMICS_TO_FETCH)

                # Create a new post
                await self.create_post()

                # Calculate seconds until next post
                seconds_between_posts = self.DAYS_BETWEEN_POSTS * 24 * 60 * 60
                logger.info(
                    f"Next post scheduled for {datetime.now() + timedelta(days=self.DAYS_BETWEEN_POSTS)}"  # noqa
                )

                # Wait for next posting time
                await asyncio.sleep(seconds_between_posts)

            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
