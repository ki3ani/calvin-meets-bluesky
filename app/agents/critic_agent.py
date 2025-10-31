"""Critic Agent - Evaluates and provides feedback on generated content"""

import logging
from typing import Dict

from app.config import get_settings
from app.services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)
settings = get_settings()


class CriticAgent:
    """Agent that evaluates content quality and provides constructive feedback"""

    def __init__(self):
        self.bedrock_service = BedrockService()
        self.min_quality_score = settings.MIN_QUALITY_SCORE
        logger.info(
            f"Initialized CriticAgent (min quality score: {self.min_quality_score})"
        )

    def evaluate_content(self, content: str, content_type: str) -> Dict:
        """
        Evaluate generated content and provide quality score and feedback.

        Args:
            content: The generated content to evaluate
            content_type: Type of content (philosophy, joke, story, poem, wisdom)

        Returns:
            Dict with 'score' (float 0-1), 'feedback' (str), and 'approved' (bool)
        """
        try:
            logger.info(f"CriticAgent evaluating {content_type} content")

            # Use Bedrock to evaluate quality
            evaluation = self.bedrock_service.evaluate_quality(content, content_type)

            score = evaluation.get("score", 0.5)
            feedback = evaluation.get("feedback", "")

            # Additional validation checks
            validation_feedback = self._additional_validation(content, content_type)
            if validation_feedback:
                feedback += f" {validation_feedback}"
                score = min(score, 0.6)  # Cap score if validation issues

            approved = score >= self.min_quality_score

            result = {
                "score": score,
                "feedback": feedback,
                "approved": approved,
            }

            logger.info(
                f"Evaluation complete: score={score:.2f}, approved={approved}"
            )
            return result

        except Exception as e:
            logger.error(f"Error in evaluate_content: {str(e)}")
            # Return a neutral evaluation if something goes wrong
            return {
                "score": 0.5,
                "feedback": f"Evaluation error: {str(e)}",
                "approved": False,
            }

    def _additional_validation(self, content: str, content_type: str) -> str:
        """
        Perform additional validation checks beyond AI evaluation.

        Args:
            content: The content to validate
            content_type: Type of content

        Returns:
            str: Feedback message if issues found, empty string otherwise
        """
        issues = []

        # Length checks
        if len(content) < 20:
            issues.append("Content too short.")
        if len(content) > 1000:
            issues.append("Content too long for social media.")

        # Check for placeholder text or common issues
        placeholder_phrases = [
            "[insert",
            "Lorem ipsum",
            "TODO",
            "PLACEHOLDER",
            "...",
        ]
        if any(phrase.lower() in content.lower() for phrase in placeholder_phrases):
            issues.append("Contains placeholder text.")

        # Type-specific validation
        if content_type == "poem":
            # Check if poem has at least some line breaks or structure
            if "\n" not in content and len(content) > 100:
                issues.append("Poem lacks structure or line breaks.")

        if content_type == "joke":
            # Very short jokes might not land
            if len(content) < 30:
                issues.append("Joke might be too brief.")

        if content_type == "story":
            # Stories should have some narrative structure
            if len(content) < 50:
                issues.append("Story too brief to have narrative arc.")

        return " ".join(issues) if issues else ""

    def suggest_improvements(self, content: str, content_type: str, score: float) -> str:
        """
        Suggest specific improvements for content that didn't meet quality standards.

        Args:
            content: The content that needs improvement
            content_type: Type of content
            score: Current quality score

        Returns:
            str: Specific suggestions for improvement
        """
        try:
            system_prompt = f"""You are a content editor specializing in {content_type} content for social media.
Your job is to provide specific, actionable feedback on how to improve content."""

            prompt = f"""Review this {content_type} content and provide 2-3 specific, actionable suggestions for improvement:

Content:
{content}

Current quality score: {score}/1.0
Target score: {self.min_quality_score}/1.0

Provide concise, specific suggestions focused on:
- Clarity and impact
- Engagement and resonance
- Style and voice
- Length and pacing

Keep suggestions brief and actionable."""

            response = self.bedrock_service.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=400,
            )

            suggestions = response.get("content", "").strip()
            return suggestions

        except Exception as e:
            logger.error(f"Error getting improvement suggestions: {str(e)}")
            return "Consider revising for clarity, impact, and engagement."

    def batch_evaluate(self, content_items: list) -> list:
        """
        Evaluate multiple content items in batch.

        Args:
            content_items: List of dicts with 'content' and 'content_type' keys

        Returns:
            list: List of evaluation results
        """
        results = []
        for item in content_items:
            try:
                evaluation = self.evaluate_content(
                    item.get("content", ""), item.get("content_type", "")
                )
                results.append(
                    {
                        "content": item.get("content"),
                        "content_type": item.get("content_type"),
                        **evaluation,
                    }
                )
            except Exception as e:
                logger.error(f"Error in batch evaluation: {str(e)}")
                results.append(
                    {
                        "content": item.get("content"),
                        "content_type": item.get("content_type"),
                        "score": 0.0,
                        "feedback": f"Error: {str(e)}",
                        "approved": False,
                    }
                )

        return results
