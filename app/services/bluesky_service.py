from datetime import datetime
import httpx
from app.config import get_settings
import base64
import mimetypes
import os

settings = get_settings()

class BlueskyService:
    def __init__(self):
        self.base_url = settings.BLUESKY_API_URL
        self.session = None
        self.jwt = None
        
    async def login(self):
        """Login to Bluesky"""
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
            return auth_data
    
    async def upload_image(self, image_path: str):
        """Upload an image to Bluesky"""
        if not self.jwt:
            await self.login()
            
        mime_type = mimetypes.guess_type(image_path)[0]
        
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
            return response.json()
    
    async def create_post(self, text: str, image_path: str = None):
        """Create a post on Bluesky"""
        if not self.jwt:
            await self.login()
            
        post_data = {
            "collection": "app.bsky.feed.post",
            "repo": settings.BLUESKY_USERNAME,
            "record": {
                "text": text,
                "$type": "app.bsky.feed.post",
                "createdAt": datetime.utcnow().isoformat()
            }
        }
        
        if image_path:
            blob = await self.upload_image(image_path)
            post_data["record"]["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": [{
                    "alt": "Calvin and Hobbes comic strip",
                    "image": blob["blob"]
                }]
            }
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {self.jwt}"},
                json=post_data
            )
            response.raise_for_status()
            return response.json()
