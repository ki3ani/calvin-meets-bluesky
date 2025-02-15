import logging
import random
from datetime import date, datetime, timedelta
from tempfile import NamedTemporaryFile

import requests
from bs4 import BeautifulSoup

from app.database import dynamodb
from app.database.models import Comic
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class ComicService:
    def __init__(self):
        self.base_url = "https://www.gocomics.com/calvinandhobbes"
        self.storage_service = StorageService()
        self.start_date = date(1985, 11, 18)  # First strip published
        self.end_date = date(1995, 12, 31)  # Last strip published

    def get_random_date(self):
        total_days = (self.end_date - self.start_date).days
        random_days = random.randint(0, total_days)  # nosec
        return self.start_date + timedelta(days=random_days)

    def fetch_calvin_and_hobbes(self, dt: datetime = None):
        try:
            if not dt:
                dt = datetime.now()
            formatted_date = dt.strftime("%Y/%m/%d")
            url = f"{self.base_url}/{formatted_date}"
            logger.info(f"Fetching comic from URL: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"  # noqa
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            comic_image = soup.find("picture", class_="item-comic-image")
            if not comic_image:
                comic_image = soup.select_one(".comic__image img")
            if comic_image:
                img_tag = (
                    comic_image.find("img")
                    if comic_image.name == "picture"
                    else comic_image
                )
                image_url = img_tag.get("src", "") or img_tag.get("data-src", "")
                if not image_url:
                    raise Exception("No image URL found")
                return {
                    "date": dt,
                    "image_url": image_url,
                    "title": f"Calvin and Hobbes - {dt.strftime('%Y-%m-%d')}",
                    "local_path": None,
                }
            raise Exception("Could not find comic image")
        except Exception as e:
            logger.error(f"Error fetching comic for {dt}: {str(e)}")
            raise

    def download_image(self, image_url: str, dt: datetime):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"  # noqa
            }
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            file_name = f"calvin_{dt.strftime('%Y%m%d')}.png"
            storage_path, _ = self.storage_service.save_file(temp_path, file_name)
            if storage_path:
                logger.info(f"Saved image to storage: {storage_path}")
                return storage_path
            else:
                raise Exception("Failed to save image to storage")
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            raise

    def get_random_unposted_comic(self):
        try:
            unposted = dynamodb.get_unposted_comics()
            if not unposted:
                logger.info("No unposted comics available")
                return None
            return random.choice(unposted)
        except Exception as e:
            logger.error(f"Error getting random unposted comic: {str(e)}")
            raise

    def save_comic(self, comic_data: dict):
        try:
            # Convert the comic date to an ISO string to use as the primary key.
            strip_date_iso = comic_data["date"].isoformat()
            existing = dynamodb.get_comic_by_strip_date(strip_date_iso)
            if existing:
                logger.info(f"Comic for {comic_data['date']} already exists")
                return existing
            storage_path = self.download_image(
                comic_data["image_url"], comic_data["date"]
            )
            comic = Comic(
                strip_date=comic_data["date"].isoformat(),
                url=comic_data["image_url"],
                title=comic_data["title"],
                local_path=storage_path,
                posted=False,
            )
            saved_item = dynamodb.save_comic(comic.to_item())
            logger.info(f"Successfully saved comic for {comic_data['date']}")
            return saved_item
        except Exception as e:
            logger.error(f"Error in save_comic: {str(e)}")
            raise

    def mark_as_posted(self, comic_id: str):
        try:
            dynamodb.mark_as_posted(comic_id)
            logger.info(f"Marked comic {comic_id} as posted")
            return comic_id
        except Exception as e:
            logger.error(f"Error marking comic as posted: {str(e)}")
            raise

    def get_unposted_comic_count(self) -> int:
        """Returns the count of unposted comics"""
        try:
            unposted_comics = dynamodb.get_unposted_comics()
            return len(unposted_comics) if unposted_comics else 0
        except Exception as e:
            logger.error(f"Error getting unposted comic count: {str(e)}")
            return 0
