from dataclasses import dataclass
from datetime import datetime


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
