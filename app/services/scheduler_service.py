import logging
import random
from datetime import datetime

from app.config import get_settings
from app.services.bluesky_service import BlueskyService
from app.services.comic_service import ComicService
from app.utils.post_formatter import PostFormatter

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.comic_service = ComicService()
        self.bluesky_service = BlueskyService()
        self.post_formatter = PostFormatter()
        self.settings = get_settings()

    def fetch_new_comics(self, count: int = 5):
        """Fetch new comics only if there are no unposted comics available"""
        try:
            unposted_comics = self.comic_service.get_unposted_comic_count()
            if unposted_comics > 0:
                logger.info(
                    f"Skipping fetch: {unposted_comics} unposted comics available."
                )
                return 0

            logger.info("No unposted comics found, fetching new comics...")

            comics_fetched = 0
            for _ in range(count):
                try:
                    random_date = self.comic_service.get_random_date()
                    fetch_datetime = datetime.combine(random_date, datetime.min.time())
                    logger.info(f"Attempting to fetch comic for {random_date}")

                    comic_data = self.comic_service.fetch_calvin_and_hobbes(
                        fetch_datetime
                    )
                    if comic_data:
                        self.comic_service.save_comic(comic_data)
                        comics_fetched += 1
                except Exception as e:
                    logger.error(f"Error fetching comic for {random_date}: {str(e)}")
                    continue

            logger.info(f"Fetched {comics_fetched} new comics.")
            return comics_fetched

        except Exception as e:
            logger.error(f"Error in fetch_new_comics: {str(e)}")
            return 0

    def create_post(self):
        """Create a new post with a random unposted comic"""
        try:
            comic = self.comic_service.get_random_unposted_comic()

            if not comic:
                logger.warning(
                    "No unposted comics available. Attempting to fetch new comics..."
                )
                fetched_count = self.fetch_new_comics(count=5)  # Fetch new comics
                if fetched_count == 0:
                    logger.error("Fetching comics failed or no new comics found.")
                    return None  # Stop if no comics were fetched

                # Try again after fetching
                comic = self.comic_service.get_random_unposted_comic()
                if not comic:
                    logger.error("Still no unposted comics after fetching. Exiting.")
                    return None

            captions = self.post_formatter.create_random_captions()
            post_text = f"{random.choice(captions)}\n\n"

            try:
                comic_date = datetime.strptime(comic["strip_date"], "%Y-%m-%d").date()
            except ValueError:
                comic_date = datetime.fromisoformat(comic["strip_date"]).date()

            post_text += self.post_formatter.create_post_text(
                comic_date, comic["title"]
            )

            logger.info(f"Creating post with comic from {comic['strip_date']}")

            result = self.bluesky_service.create_post(post_text, comic["local_path"])

            if result:
                self.comic_service.mark_as_posted(comic["strip_date"])
                logger.info(f"Successfully posted comic from {comic['strip_date']}")
                return result
            else:
                logger.error("Bluesky post creation returned None")
                return None

        except Exception as e:
            logger.error(f"Error in create_post: {str(e)}")
            return None
