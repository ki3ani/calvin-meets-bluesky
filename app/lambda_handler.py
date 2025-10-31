import json
import logging
from datetime import datetime

from app.services.content_scheduler_service import ContentSchedulerService

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def generate_content(event, context):
    """Lambda handler for generating new AI content"""
    try:
        logger.info(f"Starting AI content generation at {datetime.now()}")

        # Parse event parameters
        count = event.get("count", 5)
        content_type = event.get("content_type")  # Optional specific type

        scheduler = ContentSchedulerService()
        result = scheduler.generate_new_content(count=count, content_type=content_type)

        if result.get("skipped"):
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": result.get("message"),
                        "skipped": True,
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            }

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Successfully generated {result.get('generated', 0)} content pieces",
                    "generated": result.get("generated", 0),
                    "failed": result.get("failed", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
        }
    except Exception as e:
        logger.error(f"Error in generate_content: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
        }


def create_post(event, context):
    """Lambda handler for creating new posts from AI-generated content"""
    try:
        logger.info(f"Starting post creation at {datetime.now()}")
        scheduler = ContentSchedulerService()
        result = scheduler.create_post()

        if result and result.get("success"):
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": "Successfully created post",
                        "content_id": result.get("content_id", ""),
                        "content_type": result.get("content_type", ""),
                        "post_uri": result.get("post_uri", ""),
                        "quality_score": result.get("quality_score", 0),
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            }
        else:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "message": "No posts created - no unposted content available",
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            }
    except Exception as e:
        logger.error(f"Error in create_post: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
        }


def get_stats(event, context):
    """Lambda handler for getting content generation statistics"""
    try:
        logger.info("Fetching content statistics")
        scheduler = ContentSchedulerService()
        stats = scheduler.get_content_stats()

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "stats": stats,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
        }
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
        }


# Legacy handler names for backward compatibility
def fetch_comics(event, context):
    """Legacy handler - redirects to generate_content"""
    logger.warning("fetch_comics is deprecated, use generate_content instead")
    return generate_content(event, context)
