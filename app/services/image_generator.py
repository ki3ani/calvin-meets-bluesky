"""Image Generator - Creates AI-generated images for content"""

import logging
from tempfile import NamedTemporaryFile
from typing import Dict, Optional

from app.config import get_settings
from app.services.bedrock_service import BedrockService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)
settings = get_settings()


class ImageGenerator:
    """Service for generating AI images to accompany content"""

    def __init__(self):
        self.bedrock_service = BedrockService()
        self.storage_service = StorageService()
        self.enabled = settings.ENABLE_IMAGE_GENERATION
        logger.info(f"Initialized ImageGenerator (enabled: {self.enabled})")

    def generate_image_for_content(
        self, content: str, content_type: str, content_id: str
    ) -> Optional[Dict]:
        """
        Generate an AI image that complements the given content.

        Args:
            content: The text content to create an image for
            content_type: Type of content (philosophy, joke, story, poem, wisdom)
            content_id: ID of the content for file naming

        Returns:
            Dict with 'image_path' and 'image_prompt' or None if generation disabled/failed
        """
        if not self.enabled:
            logger.info("Image generation is disabled")
            return None

        try:
            logger.info(f"Generating image for {content_type} content")

            # Step 1: Generate an image prompt based on the content
            image_prompt = self._create_image_prompt(content, content_type)
            logger.info(f"Image prompt: {image_prompt[:100]}...")

            # Step 2: Generate the image using Stability AI
            image_data = self.bedrock_service.generate_image(
                prompt=image_prompt,
                negative_prompt=self._get_negative_prompt(content_type),
                style_preset=self._get_style_preset(content_type),
            )

            # Step 3: Save image to temporary file
            with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name

            # Step 4: Upload to S3
            file_name = f"generated_{content_id}.png"
            storage_path, _ = self.storage_service.save_file(temp_path, file_name)

            if storage_path:
                logger.info(f"Successfully generated and saved image: {storage_path}")
                return {
                    "image_path": storage_path,
                    "image_prompt": image_prompt,
                }
            else:
                logger.error("Failed to save generated image")
                return None

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            # Don't fail the whole content generation if image fails
            return None

    def _create_image_prompt(self, content: str, content_type: str) -> str:
        """
        Use Claude to create an effective image generation prompt based on the content.

        Args:
            content: The text content
            content_type: Type of content

        Returns:
            str: Image generation prompt
        """
        try:
            system_prompt = """You are an expert at creating prompts for AI image generation (Stable Diffusion).
Your job is to create concise, vivid, effective prompts that will generate beautiful, abstract, or conceptual images
that complement text content without being too literal."""

            prompt = f"""Create a Stable Diffusion image prompt for this {content_type}:

"{content}"

Requirements:
- 20-40 words maximum
- Focus on mood, atmosphere, and visual metaphors
- Avoid text in images
- Use artistic styles (watercolor, digital art, minimalist, etc.)
- Should complement the content's theme without being too literal

Generate ONLY the image prompt, no explanation."""

            response = self.bedrock_service.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=200,
            )

            image_prompt = response["content"].strip()

            # Add quality modifiers
            image_prompt += ", high quality, aesthetic, beautiful composition"

            return image_prompt

        except Exception as e:
            logger.error(f"Error creating image prompt: {str(e)}")
            # Fallback to a generic prompt based on content type
            return self._get_fallback_prompt(content_type)

    def _get_style_preset(self, content_type: str) -> str:
        """
        Get appropriate style preset for content type.

        Args:
            content_type: Type of content

        Returns:
            str: Stability AI style preset
        """
        style_map = {
            "philosophy": "digital-art",
            "joke": "comic-book",
            "story": "fantasy-art",
            "poem": "photographic",
            "wisdom": "analog-film",
        }
        return style_map.get(content_type, "digital-art")

    def _get_negative_prompt(self, content_type: str) -> str:
        """
        Get negative prompt to avoid unwanted elements.

        Args:
            content_type: Type of content

        Returns:
            str: Negative prompt
        """
        base_negative = "text, words, letters, watermark, signature, low quality, blurry, distorted"

        # Add type-specific negatives
        if content_type == "joke":
            return f"{base_negative}, serious, dark, gloomy"
        elif content_type == "philosophy":
            return f"{base_negative}, chaotic, cluttered"
        elif content_type == "poem":
            return f"{base_negative}, harsh, mechanical"

        return base_negative

    def _get_fallback_prompt(self, content_type: str) -> str:
        """
        Get a fallback image prompt if AI generation fails.

        Args:
            content_type: Type of content

        Returns:
            str: Fallback prompt
        """
        fallback_prompts = {
            "philosophy": "abstract contemplative scene, minimalist, thoughtful atmosphere, soft colors",
            "joke": "playful colorful illustration, whimsical, lighthearted, fun composition",
            "story": "imaginative narrative scene, atmospheric, dreamy, artistic storytelling",
            "poem": "ethereal poetic imagery, delicate, beautiful, soft focus",
            "wisdom": "serene inspiring landscape, peaceful, wise, calming atmosphere",
        }

        prompt = fallback_prompts.get(
            content_type, "abstract artistic composition, beautiful, aesthetic"
        )
        return f"{prompt}, high quality"

    def batch_generate_images(self, content_items: list) -> list:
        """
        Generate images for multiple content items.

        Args:
            content_items: List of dicts with 'content', 'content_type', 'content_id'

        Returns:
            list: List of results with image paths
        """
        results = []

        for item in content_items:
            try:
                result = self.generate_image_for_content(
                    content=item.get("content", ""),
                    content_type=item.get("content_type", ""),
                    content_id=item.get("content_id", ""),
                )

                results.append(
                    {
                        "content_id": item.get("content_id"),
                        "success": result is not None,
                        "image_path": result.get("image_path") if result else None,
                        "image_prompt": result.get("image_prompt") if result else None,
                    }
                )

            except Exception as e:
                logger.error(f"Error in batch image generation: {str(e)}")
                results.append(
                    {
                        "content_id": item.get("content_id"),
                        "success": False,
                        "error": str(e),
                    }
                )

        return results
