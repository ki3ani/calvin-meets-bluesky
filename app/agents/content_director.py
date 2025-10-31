"""Content Director Agent - Decides what type of content to create"""

import logging
import random
from typing import Dict, List

from app.config import get_settings
from app.database import dynamodb

logger = logging.getLogger(__name__)
settings = get_settings()


class ContentDirector:
    """Agent that decides what type of content should be created next"""

    def __init__(self):
        self.content_types = settings.CONTENT_TYPES
        logger.info("Initialized ContentDirector")

    def decide_content_type(self) -> str:
        """
        Decide what type of content to create next based on:
        - Content variety (ensure diverse content)
        - Recent posting history
        - Randomization for natural feel

        Returns:
            str: The content type to create (philosophy, joke, story, poem, wisdom)
        """
        try:
            # Get statistics about existing content
            stats = dynamodb.get_content_statistics()

            # Get counts for each type
            type_counts = stats.get("by_type", {})

            # Find the least posted content types
            min_count = min(type_counts.values()) if type_counts else 0

            # Get all types that have the minimum count (or don't exist yet)
            underrepresented_types = [
                ct for ct in self.content_types if type_counts.get(ct, 0) == min_count
            ]

            # If all types are equally represented, choose randomly
            if len(underrepresented_types) == len(self.content_types):
                chosen_type = random.choice(self.content_types)
                logger.info(f"All types equal, randomly chose: {chosen_type}")
            else:
                # Prefer underrepresented types, but with some randomness
                if random.random() < 0.8:  # 80% of the time, pick underrepresented
                    chosen_type = random.choice(underrepresented_types)
                    logger.info(f"Chose underrepresented type: {chosen_type}")
                else:  # 20% of the time, pick any type for variety
                    chosen_type = random.choice(self.content_types)
                    logger.info(f"Random variety pick: {chosen_type}")

            logger.info(
                f"ContentDirector decided: {chosen_type} (Current stats: {type_counts})"
            )
            return chosen_type

        except Exception as e:
            logger.error(f"Error in decide_content_type: {str(e)}")
            # Fallback to random selection
            return random.choice(self.content_types)

    def get_agent_for_type(self, content_type: str):
        """
        Get the appropriate agent instance for a content type.

        Args:
            content_type: The type of content to create

        Returns:
            ContentAgent: Instance of the appropriate agent
        """
        from app.agents.specialized_agents import (
            ComedianAgent,
            PhilosopherAgent,
            PoetAgent,
            StorytellerAgent,
            WisdomAgent,
        )

        agent_map = {
            "philosophy": PhilosopherAgent,
            "joke": ComedianAgent,
            "story": StorytellerAgent,
            "poem": PoetAgent,
            "wisdom": WisdomAgent,
        }

        agent_class = agent_map.get(content_type)
        if not agent_class:
            logger.warning(f"Unknown content type: {content_type}, defaulting to Philosopher")
            agent_class = PhilosopherAgent

        return agent_class()

    def generate_variety_report(self) -> Dict:
        """
        Generate a report on content variety and balance.

        Returns:
            Dict with statistics and recommendations
        """
        try:
            stats = dynamodb.get_content_statistics()
            type_counts = stats.get("by_type", {})

            # Calculate variety score (how evenly distributed are the content types)
            if type_counts:
                total = sum(type_counts.values())
                ideal_per_type = total / len(self.content_types)
                variance = sum(
                    abs(type_counts.get(ct, 0) - ideal_per_type) for ct in self.content_types
                )
                variety_score = max(0, 1 - (variance / (total * 2)))
            else:
                variety_score = 1.0

            return {
                "total_content": stats.get("total", 0),
                "posted": stats.get("posted", 0),
                "unposted": stats.get("unposted", 0),
                "by_type": type_counts,
                "variety_score": variety_score,
                "avg_quality": stats.get("avg_quality_score", 0),
            }

        except Exception as e:
            logger.error(f"Error generating variety report: {str(e)}")
            return {}
