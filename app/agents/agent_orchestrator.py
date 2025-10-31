"""Agent Orchestrator - Coordinates the multi-agent workflow"""

import logging
from typing import Dict, Optional

from app.agents.content_director import ContentDirector
from app.agents.critic_agent import CriticAgent
from app.config import get_settings
from app.database import dynamodb
from app.database.models import GeneratedContent

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentOrchestrator:
    """Orchestrates the multi-agent content generation workflow"""

    def __init__(self):
        self.director = ContentDirector()
        self.critic = CriticAgent()
        self.max_revision_attempts = 2
        logger.info("Initialized AgentOrchestrator")

    def generate_content(
        self, content_type: Optional[str] = None, max_attempts: int = 3
    ) -> Dict:
        """
        Orchestrate the full content generation workflow with multiple agents.

        Workflow:
        1. ContentDirector decides content type (or use provided type)
        2. Specialized agent generates content
        3. CriticAgent evaluates content
        4. If quality too low, agent revises (up to max_revision_attempts)
        5. Save to DynamoDB
        6. Return final content

        Args:
            content_type: Optional specific content type, otherwise Director decides
            max_attempts: Maximum attempts to generate acceptable content

        Returns:
            Dict with generated content details and metadata
        """
        try:
            # Step 1: Decide content type
            if not content_type:
                content_type = self.director.decide_content_type()
                logger.info(f"Director chose content type: {content_type}")
            else:
                logger.info(f"Using specified content type: {content_type}")

            # Step 2: Get the appropriate agent
            creator_agent = self.director.get_agent_for_type(content_type)
            logger.info(f"Using agent: {creator_agent.agent_name}")

            best_content = None
            best_score = 0.0
            attempt = 0

            while attempt < max_attempts:
                attempt += 1
                logger.info(f"Generation attempt {attempt}/{max_attempts}")

                # Step 3: Generate content
                generated = creator_agent.generate_content()
                content_text = generated["text"]

                # Validate basic structure
                if not creator_agent.validate_content(content_text):
                    logger.warning(
                        f"Attempt {attempt}: Content failed basic validation"
                    )
                    continue

                # Step 4: Critic evaluates
                evaluation = self.critic.evaluate_content(content_text, content_type)
                score = evaluation["score"]
                feedback = evaluation["feedback"]
                approved = evaluation["approved"]

                logger.info(
                    f"Attempt {attempt}: Score={score:.2f}, Approved={approved}"
                )

                # Track best content so far
                if score > best_score:
                    best_score = score
                    best_content = {
                        "text": content_text,
                        "score": score,
                        "feedback": feedback,
                        "approved": approved,
                        "agent_name": creator_agent.agent_name,
                        "content_type": content_type,
                        "revision_count": 0,
                    }

                # If approved, we're done!
                if approved:
                    logger.info(f"Content approved on attempt {attempt}!")
                    break

                # Try to improve if we have revision attempts left
                if attempt < max_attempts:
                    logger.info("Content not approved, requesting revision...")
                    try:
                        improved = creator_agent.improve_content(
                            content_text, feedback
                        )
                        improved_text = improved["text"]

                        # Re-evaluate improved content
                        improved_eval = self.critic.evaluate_content(
                            improved_text, content_type
                        )
                        improved_score = improved_eval["score"]

                        logger.info(
                            f"Revision score: {improved_score:.2f} (was {score:.2f})"
                        )

                        # Update best if improved version is better
                        if improved_score > best_score:
                            best_score = improved_score
                            best_content = {
                                "text": improved_text,
                                "score": improved_score,
                                "feedback": improved_eval["feedback"],
                                "approved": improved_eval["approved"],
                                "agent_name": creator_agent.agent_name,
                                "content_type": content_type,
                                "revision_count": attempt,
                            }

                            # Check if revision got us to approval
                            if improved_eval["approved"]:
                                logger.info("Content approved after revision!")
                                break

                    except Exception as e:
                        logger.error(f"Error during content improvement: {str(e)}")

            # Step 5: Save the best content we generated
            if best_content:
                content_obj = GeneratedContent(
                    content_type=best_content["content_type"],
                    agent_name=best_content["agent_name"],
                    text_content=best_content["text"],
                    quality_score=best_content["score"],
                    critic_feedback=best_content["feedback"],
                    revision_count=best_content["revision_count"],
                    posted=False,
                )

                saved_item = dynamodb.save_generated_content(content_obj.to_item())

                logger.info(
                    f"Saved content to DB: {saved_item['content_id']} "
                    f"(score: {best_score:.2f}, approved: {best_content['approved']})"
                )

                return {
                    "success": True,
                    "content_id": saved_item["content_id"],
                    "content": best_content["text"],
                    "content_type": content_type,
                    "agent_name": best_content["agent_name"],
                    "quality_score": best_score,
                    "approved": best_content["approved"],
                    "attempts": attempt,
                    "revision_count": best_content["revision_count"],
                }
            else:
                logger.error("Failed to generate acceptable content")
                return {
                    "success": False,
                    "error": "Failed to generate content after all attempts",
                }

        except Exception as e:
            logger.error(f"Error in generate_content workflow: {str(e)}")
            return {"success": False, "error": str(e)}

    def generate_batch_content(self, count: int = 5, content_type: Optional[str] = None) -> Dict:
        """
        Generate multiple pieces of content in a batch.

        Args:
            count: Number of content pieces to generate
            content_type: Optional specific content type for all pieces

        Returns:
            Dict with batch generation results
        """
        try:
            logger.info(f"Starting batch generation: {count} pieces")

            results = []
            successful = 0
            failed = 0

            for i in range(count):
                logger.info(f"Generating batch item {i+1}/{count}")

                result = self.generate_content(content_type=content_type)

                if result.get("success"):
                    successful += 1
                    results.append(result)
                else:
                    failed += 1
                    logger.warning(f"Batch item {i+1} failed: {result.get('error')}")

            logger.info(f"Batch complete: {successful} successful, {failed} failed")

            return {
                "total": count,
                "successful": successful,
                "failed": failed,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Error in batch generation: {str(e)}")
            return {"total": count, "successful": 0, "failed": count, "error": str(e)}

    def get_best_unposted_content(self) -> Optional[Dict]:
        """
        Get the highest quality unposted content.

        Returns:
            Dict with content details or None if no unposted content
        """
        try:
            unposted = dynamodb.get_unposted_content()

            if not unposted:
                logger.info("No unposted content available")
                return None

            # Sort by quality score (highest first)
            sorted_content = sorted(
                unposted, key=lambda x: x.get("quality_score", 0), reverse=True
            )

            best = sorted_content[0]
            logger.info(
                f"Selected best unposted content: {best['content_id']} "
                f"(score: {best.get('quality_score', 0):.2f})"
            )

            return best

        except Exception as e:
            logger.error(f"Error getting best unposted content: {str(e)}")
            return None

    def get_workflow_stats(self) -> Dict:
        """
        Get statistics about the content generation workflow.

        Returns:
            Dict with workflow statistics
        """
        try:
            content_stats = dynamodb.get_content_statistics()
            variety_report = self.director.generate_variety_report()

            return {
                "content_stats": content_stats,
                "variety_report": variety_report,
                "quality_threshold": settings.MIN_QUALITY_SCORE,
            }

        except Exception as e:
            logger.error(f"Error getting workflow stats: {str(e)}")
            return {}
