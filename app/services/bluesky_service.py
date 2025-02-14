from datetime import datetime
import httpx
from app.config import get_settings
import base64
import mimetypes
import os
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class BlueskyService:
    def __init__(self):
        self.base_url = settings.BLUESKY_API_URL
        self.session = None
        self.jwt = None
        self.did = None
        
    async def login(self):
        """Login to Bluesky and get DID"""
        try:
            logger.info("Attempting to login to Bluesky")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}com.atproto.server.createSession",
                    json={
                        "identifier": settings.BLUESKY_USERNAME,
                        "password": settings.BLUESKY_PASSWORD
                    }
                )
                response.raise_for_status()
                auth_data = response.json()
                self.jwt = auth_data.get('accessJwt')
                self.did = auth_data.get('did')  # Get the DID from login response
                logger.info(f"Successfully logged in to Bluesky with DID: {self.did}")
                return auth_data
        except Exception as e:
            logger.error(f"Failed to login to Bluesky: {str(e)}")
            raise
    
    async def upload_image(self, image_path: str):
        """Upload an image to Bluesky"""
        try:
            if not self.jwt:
                await self.login()
                
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
                
            mime_type = mimetypes.guess_type(image_path)[0]
            if not mime_type:
                mime_type = 'image/png'  # Default to PNG if type can't be determined
            
            logger.info(f"Uploading image: {image_path}")
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}com.atproto.repo.uploadBlob",
                    headers={
                        "Authorization": f"Bearer {self.jwt}",
                        "Content-Type": mime_type
                    },
                    content=image_data
                )
                response.raise_for_status()
                logger.info("Successfully uploaded image")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to upload image: {str(e)}")
            raise
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime in RFC-3339 format with 'Z' timezone indicator"""
        return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    async def create_post(self, text: str, image_path: str = None):
        """Create a post on Bluesky"""
        try:
            if not self.jwt or not self.did:
                await self.login()
            
            logger.info(f"Creating post with text length: {len(text)}")
            
            post_data = {
                "collection": "app.bsky.feed.post",
                "repo": self.did,  # Use DID instead of username
                "record": {
                    "text": text,
                    "$type": "app.bsky.feed.post",
                    "createdAt": self._format_datetime(datetime.utcnow())
                }
            }
            
            if image_path:
                try:
                    blob = await self.upload_image(image_path)
                    post_data["record"]["embed"] = {
                        "$type": "app.bsky.embed.images",
                        "images": [{
                            "alt": "Calvin and Hobbes comic strip",
                            "image": blob["blob"]
                        }]
                    }
                except Exception as e:
                    logger.error(f"Failed to upload image for post: {str(e)}")
                    raise
            
            logger.info(f"Sending post to Bluesky using DID: {self.did}")
            logger.debug(f"Post data: {post_data}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}com.atproto.repo.createRecord",
                    headers={"Authorization": f"Bearer {self.jwt}"},
                    json=post_data
                )
                response.raise_for_status()
                logger.info("Successfully created post")
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to create post: {str(e)}")
            if isinstance(e, httpx.HTTPError):
                logger.error(f"HTTP Status Code: {e.response.status_code}")
                logger.error(f"Response Text: {e.response.text}")
            raise