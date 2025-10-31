import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from app.services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)


class ContentAgent(ABC):
    """Base class for all content generation agents"""

    def __init__(self, agent_name: str, content_type: str):
        self.agent_name = agent_name
        self.content_type = content_type
        self.bedrock_service = BedrockService()
        logger.info(f"Initialized {self.agent_name}")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt that defines this agent's personality and role"""
        pass

    @abstractmethod
    def get_generation_prompt(self) -> str:
        """Return the prompt for generating content"""
        pass

    def generate_content(self, additional_context: Optional[str] = None) -> Dict:
        """
        Generate content using the agent's prompts and Bedrock.

        Args:
            additional_context: Optional additional context for generation

        Returns:
            Dict with 'text', 'agent_name', 'content_type' keys
        """
        try:
            system_prompt = self.get_system_prompt()
            generation_prompt = self.get_generation_prompt()

            if additional_context:
                generation_prompt += f"\n\nAdditional context: {additional_context}"

            logger.info(f"{self.agent_name} generating {self.content_type} content")

            response = self.bedrock_service.generate_text(
                prompt=generation_prompt,
                system_prompt=system_prompt,
            )

            content_text = response.get("content", "").strip()

            if not content_text:
                raise Exception("Generated content is empty")

            logger.info(
                f"{self.agent_name} successfully generated content ({len(content_text)} chars)"
            )

            return {
                "text": content_text,
                "agent_name": self.agent_name,
                "content_type": self.content_type,
                "usage": response.get("usage", {}),
            }

        except Exception as e:
            logger.error(f"Error in {self.agent_name}.generate_content: {str(e)}")
            raise

    def improve_content(self, original_content: str, feedback: str) -> Dict:
        """
        Improve content based on critic feedback.

        Args:
            original_content: The original generated content
            feedback: Feedback from the critic agent

        Returns:
            Dict with improved content
        """
        try:
            improvement_prompt = f"""Your previous content:
{original_content}

Feedback received:
{feedback}

Please improve the content based on this feedback while maintaining your unique voice and style. Generate an improved version."""

            logger.info(f"{self.agent_name} improving content based on feedback")

            response = self.bedrock_service.generate_text(
                prompt=improvement_prompt,
                system_prompt=self.get_system_prompt(),
            )

            improved_text = response.get("content", "").strip()

            return {
                "text": improved_text,
                "agent_name": self.agent_name,
                "content_type": self.content_type,
                "improved": True,
            }

        except Exception as e:
            logger.error(f"Error improving content: {str(e)}")
            # Return original content if improvement fails
            return {
                "text": original_content,
                "agent_name": self.agent_name,
                "content_type": self.content_type,
                "improved": False,
            }

    def validate_content(self, content: str) -> bool:
        """
        Validate that content meets basic requirements.

        Args:
            content: The content to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not content or len(content.strip()) == 0:
            logger.warning("Content is empty")
            return False

        # Check length - should be suitable for social media (not too long)
        if len(content) > 1000:
            logger.warning(f"Content too long: {len(content)} chars")
            return False

        # Minimum length check
        if len(content) < 20:
            logger.warning(f"Content too short: {len(content)} chars")
            return False

        return True
