import os
from pathlib import Path
from typing import Optional, Tuple

from ..config import get_settings
from .s3_service import S3Service


class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.s3_service = None
        if self.settings.USE_S3_STORAGE:
            self.s3_service = S3Service(
                bucket_name=self.settings.S3_BUCKET_NAME,
                aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.settings.AWS_REGION,
            )

    async def save_file(
        self, file_path: str, destination_path: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Save a file to either S3 or local storage
        Returns: (storage_path, access_url)
        """
        if not destination_path:
            destination_path = os.path.basename(file_path)

        if self.settings.USE_S3_STORAGE:
            # Upload to S3
            success = self.s3_service.upload_file(file_path, destination_path)
            if success:
                storage_path = self.s3_service.get_permanent_file_url(destination_path)
                access_url = self.s3_service.get_file_url(destination_path)
                return storage_path, access_url
            return None, None
        else:
            # Save locally
            local_path = Path("comic_images") / destination_path
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file to destination
            with open(file_path, "rb") as source, open(local_path, "wb") as dest:
                dest.write(source.read())

            return str(local_path), str(local_path)

    async def get_file_url(self, storage_path: str) -> str:
        """Get the URL for a file"""
        if self.settings.USE_S3_STORAGE and storage_path.startswith("s3://"):
            # Extract the object name from the s3:// URL
            object_name = storage_path.split("/", 3)[-1]
            return self.s3_service.get_file_url(object_name)
        else:
            return storage_path  # For local storage, return the local path

    async def delete_file(self, storage_path: str) -> bool:
        """Delete a file from storage"""
        if self.settings.USE_S3_STORAGE and storage_path.startswith("s3://"):
            object_name = storage_path.split("/", 3)[-1]
            return self.s3_service.delete_file(object_name)
        else:
            try:
                os.remove(storage_path)
                return True
            except Exception as e:
                print(f"Error deleting local file: {e}")
                return False
