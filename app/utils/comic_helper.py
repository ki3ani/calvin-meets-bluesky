import logging
import os
import random
from datetime import datetime, timedelta
from typing import List

from PIL import Image

logger = logging.getLogger(__name__)


class ComicHelper:
    def __init__(self, image_dir: str = "comic_images"):
        self.image_dir = image_dir

    def validate_image(self, image_path: str) -> bool:
        """Validate if image exists and is a valid image file"""
        try:
            if not os.path.exists(image_path):
                return False
            Image.open(image_path).verify()
            return True
        except Exception as e:
            logger.error(f"Image validation failed for {image_path}: {str(e)}")
            return False

    def get_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[datetime]:
        """Get list of dates between start and end date"""
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        return date_list

    def generate_filename(self, date: datetime) -> str:
        """Generate filename for comic image"""
        return f"calvin_{date.strftime('%Y%m%d')}.png"

    def get_image_path(self, date: datetime) -> str:
        """Get full path for comic image"""
        filename = self.generate_filename(date)
        return os.path.join(self.image_dir, filename)

    @staticmethod
    def is_sunday(date: datetime) -> bool:
        """Check if date is a Sunday (Sunday comics are special)"""
        return date.weekday() == 6

    @staticmethod
    def get_random_hashtags(count: int = 3) -> List[str]:
        """Get random hashtags for posts"""
        hashtag_pool = [
            "CalvinAndHobbes",
            "Comics",
            "Nostalgia",
            "BillWatterson",
            "Comics",
            "CalvinHobbes",
            "NewspaperComics",
            "ComicStrip",
            "Childhood",
            "ClassicComics",
            "Tiger",
            "Imagination",
            "Adventure",
            "Philosophy",
            "Wisdom",
            "Creativity",
        ]
        return random.sample(hashtag_pool, min(count, len(hashtag_pool)))

    @staticmethod
    def create_caption(date: datetime, is_sunday: bool = False) -> str:
        """Create caption for comic post"""
        base_captions = [
            "Join Calvin and Hobbes on another adventure! 🌟",
            "Time for some childhood nostalgia! 📚",
            "What mischief will Calvin get into today? 🎨",
            "Philosophy with Calvin and Hobbes! 🤔",
            "Ready for some imagination and wonder? ✨",
        ]

        sunday_captions = [
            "It's Sunday! Time for a special colored adventure! 🎨",
            "Sunday means extra special Calvin and Hobbes! 🌈",
            "Enjoy this Sunday's colorful journey! 🎪",
        ]

        caption_pool = sunday_captions if is_sunday else base_captions
        return random.choice(caption_pool)
