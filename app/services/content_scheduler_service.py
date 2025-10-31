"""Content Scheduler Service - Manages AI-generated content creation and posting"""

import logging
from typing import Dict, Optional

from app.agents.agent_orchestrator import AgentOrchestrator
from app.config import get_settings
from app.database import dynamodb
from app.services.bluesky_service import BlueskyService
from app.services.image_generator import ImageGenerator

logger = logging.getLogger(__name__)


class ContentSchedulerService:
    """Service for scheduling and managing AI-generated content"""

    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.bluesky_service = BlueskyService()
        self.image_generator = ImageGenerator()
        self.settings = get_settings()
        logger.info("Initialized ContentSchedulerService")

    def generate_new_content(self, count: int = 5, content_type: Optional[str] = None) -> Dict:
        """
        Generate new AI content using the agent orchestrator.

        Args:
            count: Number of content pieces to generate
            content_type: Optional specific content type, otherwise varies

        Returns:
            Dict with generation results
        """
        try:
            logger.info(f"Starting content generation: {count} pieces")

            # Check if we already have enough unposted content
            unposted = dynamodb.get_unposted_content()
            unposted_count = len(unposted) if unposted else 0

            if unposted_count >= 10:  # Arbitrary threshold
                logger.info(
                    f"Skipping generation: {unposted_count} unposted content already available"
                )
                return {
                    "generated": 0,
                    "message": f"Sufficient unposted content exists ({unposted_count})",
                    "skipped": True,
                }

            # Generate batch content
            result = self.orchestrator.generate_batch_content(
                count=count, content_type=content_type
            )

            # Optionally generate images for successful content
            if self.settings.ENABLE_IMAGE_GENERATION and result.get("successful", 0) > 0:
                logger.info("Generating images for new content...")
                self._generate_images_for_batch(result.get("results", []))

            logger.info(
                f"Content generation complete: {result.get('successful', 0)} successful"
            )

            return {
                "generated": result.get("successful", 0),
                "failed": result.get("failed", 0),
                "total": result.get("total", 0),
                "results": result.get("results", []),
                "skipped": False,
            }

        except Exception as e:
            logger.error(f"Error in generate_new_content: {str(e)}")
            return {
                "generated": 0,
                "failed": count,
                "error": str(e),
                "skipped": False,
            }

    def _generate_images_for_batch(self, content_results: list):
        """
        Generate images for a batch of content.

        Args:
            content_results: List of content generation results
        """
        try:
            image_items = []
            for result in content_results:
                if result.get("success"):
                    image_items.append(
                        {
                            "content": result.get("content", ""),
                            "content_type": result.get("content_type", ""),
                            "content_id": result.get("content_id", ""),
                        }
                    )

            if not image_items:
                return

            image_results = self.image_generator.batch_generate_images(image_items)

            # Update DynamoDB with image paths
            for img_result in image_results:
                if img_result.get("success"):
                    content_id = img_result.get("content_id")
                    content_item = dynamodb.get_content_by_id(content_id)

                    if content_item:
                        # Update with image info
                        content_item["image_path"] = img_result.get("image_path")
                        content_item["image_prompt"] = img_result.get("image_prompt")
                        dynamodb.save_generated_content(content_item)
                        logger.info(f"Updated content {content_id} with image")

        except Exception as e:
            logger.error(f"Error generating batch images: {str(e)}")

    def create_post(self) -> Optional[Dict]:
        """
        Create a new Bluesky post from the best available unposted content.

        Returns:
            Dict with post result or None if no content available
        """
        try:
            logger.info("Creating new post from AI-generated content")

            # Get the best unposted content
            content = self.orchestrator.get_best_unposted_content()

            if not content:
                logger.warning("No unposted content available. Generating new content...")

                # Generate new content on-demand
                gen_result = self.generate_new_content(count=3)

                if gen_result.get("generated", 0) == 0:
                    logger.error("Failed to generate new content")
                    return None

                # Try again to get unposted content
                content = self.orchestrator.get_best_unposted_content()

                if not content:
                    logger.error("Still no content available after generation")
                    return None

            # Format the post text
            post_text = self._format_post_text(content)

            # Get image path if available
            image_path = content.get("image_path")

            logger.info(
                f"Creating post for content {content['content_id']} "
                f"(type: {content['content_type']}, has_image: {image_path is not None})"
            )

            # Post to Bluesky
            result = self.bluesky_service.create_post(post_text, image_path)

            if result:
                # Mark as posted
                post_uri = result.get("uri", "")
                dynamodb.mark_content_as_posted(content["content_id"], post_uri)

                logger.info(
                    f"Successfully posted content {content['content_id']} to Bluesky"
                )

                return {
                    "success": True,
                    "content_id": content["content_id"],
                    "content_type": content["content_type"],
                    "post_uri": post_uri,
                    "quality_score": content.get("quality_score", 0),
                }
            else:
                logger.error("Bluesky post creation returned None")
                return None

        except Exception as e:
            logger.error(f"Error in create_post: {str(e)}")
            return None

    def _format_post_text(self, content: Dict) -> str:
        """
        Format content for posting to Bluesky.

        Args:
            content: Content dict from database

        Returns:
            str: Formatted post text
        """
        text = content.get("text_content", "")

        # Add subtle branding/context based on content type
        content_type = content.get("content_type", "")

        # Optional: Add hashtags or emoji based on content type
        type_emoji = {
            "philosophy": "💭",
            "joke": "😄",
            "story": "📖",
            "poem": "✨",
            "wisdom": "🌟",
        }

        emoji = type_emoji.get(content_type, "")

        # Format: emoji + text (keep it clean and simple)
        if emoji:
            formatted = f"{emoji} {text}"
        else:
            formatted = text

        return formatted

    def get_content_stats(self) -> Dict:
        """
        Get statistics about content generation and posting.

        Returns:
            Dict with comprehensive statistics
        """
        try:
            workflow_stats = self.orchestrator.get_workflow_stats()
            content_stats = dynamodb.get_content_statistics()

            return {
                "workflow_stats": workflow_stats,
                "content_stats": content_stats,
                "image_generation_enabled": self.settings.ENABLE_IMAGE_GENERATION,
            }

        except Exception as e:
            logger.error(f"Error getting content stats: {str(e)}")
            return {}

    def generate_content_on_demand(self, content_type: str) -> Dict:
        """
        Generate a specific type of content on demand (for testing/manual use).

        Args:
            content_type: Type of content to generate

        Returns:
            Dict with generation result
        """
        try:
            logger.info(f"On-demand generation requested: {content_type}")

            result = self.orchestrator.generate_content(content_type=content_type)

            # Generate image if enabled and content generated successfully
            if (
                self.settings.ENABLE_IMAGE_GENERATION
                and result.get("success")
                and result.get("content_id")
            ):
                image_result = self.image_generator.generate_image_for_content(
                    content=result.get("content", ""),
                    content_type=content_type,
                    content_id=result.get("content_id"),
                )

                if image_result:
                    # Update content with image
                    content_item = dynamodb.get_content_by_id(result["content_id"])
                    if content_item:
                        content_item["image_path"] = image_result["image_path"]
                        content_item["image_prompt"] = image_result["image_prompt"]
                        dynamodb.save_generated_content(content_item)
                        result["image_path"] = image_result["image_path"]

            return result

        except Exception as e:
            logger.error(f"Error in on-demand generation: {str(e)}")
            return {"success": False, "error": str(e)}
