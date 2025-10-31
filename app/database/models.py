import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Comic:
    strip_date: str
    url: str
    title: str
    local_path: str
    posted: bool = False
    created_at: str = None
    updated_at: str = None

    def to_item(self):
        now = datetime.utcnow().isoformat()
        return {
            "strip_date": self.strip_date,
            "url": self.url,
            "title": self.title,
            "local_path": self.local_path,
            "posted": self.posted,
            "created_at": self.created_at or now,
            "updated_at": self.updated_at or now,
        }


@dataclass
class GeneratedContent:
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_type: str = ""  # philosophy, joke, story, poem, wisdom
    agent_name: str = ""
    text_content: str = ""
    image_path: Optional[str] = None
    image_prompt: Optional[str] = None
    created_at: str = None
    posted: bool = False
    posted_at: Optional[str] = None
    quality_score: float = 0.0
    critic_feedback: Optional[str] = None
    revision_count: int = 0
    bluesky_post_uri: Optional[str] = None

    def to_item(self):
        now = datetime.utcnow().isoformat()
        item = {
            "content_id": self.content_id,
            "content_type": self.content_type,
            "agent_name": self.agent_name,
            "text_content": self.text_content,
            "created_at": self.created_at or now,
            "posted": self.posted,
            "quality_score": self.quality_score,
            "revision_count": self.revision_count,
        }

        # Only add optional fields if they have values
        if self.image_path:
            item["image_path"] = self.image_path
        if self.image_prompt:
            item["image_prompt"] = self.image_prompt
        if self.posted_at:
            item["posted_at"] = self.posted_at
        if self.critic_feedback:
            item["critic_feedback"] = self.critic_feedback
        if self.bluesky_post_uri:
            item["bluesky_post_uri"] = self.bluesky_post_uri

        return item

    @classmethod
    def from_item(cls, item: dict):
        """Create a GeneratedContent instance from a DynamoDB item"""
        return cls(
            content_id=item.get("content_id", str(uuid.uuid4())),
            content_type=item.get("content_type", ""),
            agent_name=item.get("agent_name", ""),
            text_content=item.get("text_content", ""),
            image_path=item.get("image_path"),
            image_prompt=item.get("image_prompt"),
            created_at=item.get("created_at"),
            posted=item.get("posted", False),
            posted_at=item.get("posted_at"),
            quality_score=item.get("quality_score", 0.0),
            critic_feedback=item.get("critic_feedback"),
            revision_count=item.get("revision_count", 0),
            bluesky_post_uri=item.get("bluesky_post_uri"),
        )
