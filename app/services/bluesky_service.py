import logging
import mimetypes
import os
from datetime import datetime
from tempfile import NamedTemporaryFile

import requests

from app.config import get_settings
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)
settings = get_settings()


class BlueskyService:
    def __init__(self):
        self.base_url = settings.BLUESKY_API_URL
        self.session = None
        self.jwt = None
        self.did = None
        self.storage_service = StorageService()

    def login(self):
        """Login to Bluesky and get DID"""
        try:
            logger.info("Attempting to login to Bluesky")
            response = requests.post(
                f"{self.base_url}com.atproto.server.createSession",
                json={
                    "identifier": settings.BLUESKY_USERNAME,
                    "password": settings.BLUESKY_PASSWORD,
                },
                timeout=30,
            )
            response.raise_for_status()
            auth_data = response.json()
            self.jwt = auth_data.get("accessJwt")
            self.did = auth_data.get("did")
            logger.info(f"Successfully logged in to Bluesky with DID: {self.did}")
            return auth_data
        except Exception as e:
            logger.error(f"Failed to login to Bluesky: {str(e)}")
            raise Exception(f"Failed to login to Bluesky: {str(e)}")

    def upload_image(self, image_path: str):
        """Upload an image to Bluesky"""
        try:
            if not self.jwt:
                self.login()

            # Handle S3 paths
            temp_file_path = None
            try:
                if image_path.startswith("s3://"):
                    # Get content from S3
                    image_data = self.storage_service.get_file_content(image_path)
                    if not image_data:
                        raise FileNotFoundError(
                            f"Image file not found in S3: {image_path}"
                        )

                    # Save to temporary file
                    with NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                        temp_file.write(image_data)
                        temp_file.flush()
                        temp_file_path = temp_file.name
                        image_path = temp_file_path

                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Image file not found: {image_path}")

                mime_type = mimetypes.guess_type(image_path)[0]
                if not mime_type:
                    mime_type = "image/png"

                logger.info(f"Uploading image: {image_path}")

                with open(image_path, "rb") as f:
                    image_data = f.read()

                response = requests.post(
                    f"{self.base_url}com.atproto.repo.uploadBlob",
                    headers={
                        "Authorization": f"Bearer {self.jwt}",
                        "Content-Type": mime_type,
                    },
                    data=image_data,
                    timeout=30,
                )
                response.raise_for_status()
                logger.info("Successfully uploaded image")
                return response.json()

            finally:
                # Clean up temporary file if it was created
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temporary file: {e}")

        except Exception as e:
            logger.error(f"Failed to upload image: {str(e)}")
            raise Exception(f"Failed to upload image: {str(e)}")

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime in RFC-3339 format with 'Z' timezone indicator"""
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def create_post(self, text: str, image_path: str = None):
        """Create a post on Bluesky"""
        try:
            if not self.jwt or not self.did:
                self.login()

            logger.info(f"Creating post with text length: {len(text)}")

            post_data = {
                "collection": "app.bsky.feed.post",
                "repo": self.did,
                "record": {
                    "text": text,
                    "$type": "app.bsky.feed.post",
                    "createdAt": self._format_datetime(datetime.utcnow()),
                },
            }

            if image_path:
                try:
                    blob = self.upload_image(image_path)
                    post_data["record"]["embed"] = {
                        "$type": "app.bsky.embed.images",
                        "images": [
                            {
                                "alt": "Calvin and Hobbes comic strip",
                                "image": blob["blob"],
                            }
                        ],
                    }
                except Exception as e:
                    logger.error(f"Failed to upload image for post: {str(e)}")
                    raise Exception(f"Failed to upload image for post: {str(e)}")

            logger.info(f"Sending post to Bluesky using DID: {self.did}")
            logger.debug(f"Post data: {post_data}")

            response = requests.post(
                f"{self.base_url}com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {self.jwt}"},
                json=post_data,
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Successfully created post")
            return response.json()

        except Exception as e:
            logger.error(f"Failed to create post: {str(e)}")
            if hasattr(e, "response"):
                logger.error(f"HTTP Status Code: {e.response.status_code}")
                logger.error(f"Response Text: {e.response.text}")
            raise Exception(f"Failed to create post: {str(e)}")
