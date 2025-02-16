import json
import logging
from datetime import datetime

from app.services.scheduler_service import SchedulerService

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def fetch_comics(event, context):
    """Lambda handler for fetching new comics"""
    try:
        logger.info(f"Starting comic fetch at {datetime.now()}")
        scheduler = SchedulerService()
        comics_fetched = scheduler.fetch_new_comics(count=5)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Successfully fetched {comics_fetched} comics",
                    "timestamp": datetime.now().isoformat(),
                }
            ),
        }
    except Exception as e:
        logger.error(f"Error in fetch_comics: {str(e)}")
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
    """Lambda handler for creating new posts"""
    try:
        logger.info(f"Starting post creation at {datetime.now()}")
        scheduler = SchedulerService()
        result = scheduler.create_post()

        if result:
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": "Successfully created post",
                        "postId": str(result.get("uri", "")),
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            }
        else:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "message": "No posts created - no unposted comics available",
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
