from datetime import datetime
from typing import Optional


class PostFormatter:
    @staticmethod
    def create_post_text(comic_date: datetime, title: Optional[str] = None) -> str:
        """Create post text with comic information"""
        date_str = comic_date.strftime("%B %d, %Y")

        lines = [
            f"📖 Calvin and Hobbes - {date_str}",
        ]

        if title:
            lines.append(f"\n{title}")

        lines.extend(
            ["\n#CalvinAndHobbes #Comics #Nostalgia", "Original by Bill Watterson"]
        )

        return "\n".join(lines)

    @staticmethod
    def create_random_captions() -> list:
        """Return a list of random Calvin and Hobbes related captions"""
        captions = [
            "Time for some Calvin and Hobbes wisdom! 🐯",
            "Starting the day with Calvin's adventures! 🌟",
            "A dose of childhood nostalgia coming up! 📚",
            "Philosophy with Calvin and Hobbes! 🤔",
            "Time to explore with Calvin and his tiger friend! 🎨",
            "Ready for some Calvin and Hobbes magic? ✨",
            "Let's see what trouble Calvin's getting into today! 🌍",
            "Another classic Calvin and Hobbes moment! 🌟",
            "Time for imagination and adventure! 🚀",
            "Join Calvin and Hobbes in today's exploration! 🗺️",
        ]
        return captions
