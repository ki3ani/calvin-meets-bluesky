import os
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Attr

DYNAMODB_REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "Comics")
CONTENT_TABLE_NAME = os.getenv("DYNAMODB_CONTENT_TABLE", "GeneratedContent")

dynamodb = boto3.resource("dynamodb", region_name=DYNAMODB_REGION)
table = dynamodb.Table(TABLE_NAME)
content_table = dynamodb.Table(CONTENT_TABLE_NAME)


def init_db():
    pass


def save_comic(item: dict):
    """Save a comic record to DynamoDB."""
    table.put_item(Item=item)
    return item


def get_comic_by_strip_date(strip_date: str):
    """Retrieve a comic by its strip_date (primary key)."""
    response = table.get_item(Key={"strip_date": strip_date})
    return response.get("Item")


def get_unposted_comics():
    """Return a list of comics where 'posted' is False."""
    response = table.scan(FilterExpression=Attr("posted").eq(False))
    return response.get("Items", [])


def mark_as_posted(strip_date: str):
    """Mark a comic as posted given its strip_date."""
    table.update_item(
        Key={"strip_date": strip_date},
        UpdateExpression="SET posted = :val, updated_at = :now",
        ExpressionAttributeValues={
            ":val": True,
            ":now": __import__("datetime").datetime.utcnow().isoformat(),
        },
    )


# ========== Generated Content Functions ==========


def save_generated_content(item: dict):
    """Save a generated content record to DynamoDB."""
    content_table.put_item(Item=item)
    return item


def get_content_by_id(content_id: str):
    """Retrieve generated content by its content_id (primary key)."""
    response = content_table.get_item(Key={"content_id": content_id})
    return response.get("Item")


def get_unposted_content(content_type: str = None):
    """
    Return a list of generated content where 'posted' is False.
    Optionally filter by content_type.
    """
    if content_type:
        response = content_table.scan(
            FilterExpression=Attr("posted").eq(False) & Attr("content_type").eq(content_type)
        )
    else:
        response = content_table.scan(FilterExpression=Attr("posted").eq(False))
    return response.get("Items", [])


def get_content_by_type(content_type: str):
    """Get all content of a specific type."""
    response = content_table.scan(FilterExpression=Attr("content_type").eq(content_type))
    return response.get("Items", [])


def mark_content_as_posted(content_id: str, post_uri: str = None):
    """Mark generated content as posted."""
    update_expression = "SET posted = :val, posted_at = :now"
    expression_values = {
        ":val": True,
        ":now": datetime.utcnow().isoformat(),
    }

    if post_uri:
        update_expression += ", bluesky_post_uri = :uri"
        expression_values[":uri"] = post_uri

    content_table.update_item(
        Key={"content_id": content_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values,
    )


def update_content_quality(content_id: str, quality_score: float, critic_feedback: str = None):
    """Update the quality score and optional critic feedback for content."""
    update_expression = "SET quality_score = :score"
    expression_values = {":score": quality_score}

    if critic_feedback:
        update_expression += ", critic_feedback = :feedback"
        expression_values[":feedback"] = critic_feedback

    content_table.update_item(
        Key={"content_id": content_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values,
    )


def get_content_statistics():
    """Get statistics about generated content."""
    response = content_table.scan()
    items = response.get("Items", [])

    stats = {
        "total": len(items),
        "posted": sum(1 for item in items if item.get("posted", False)),
        "unposted": sum(1 for item in items if not item.get("posted", False)),
        "by_type": {},
        "avg_quality_score": 0,
    }

    # Count by type
    for item in items:
        content_type = item.get("content_type", "unknown")
        stats["by_type"][content_type] = stats["by_type"].get(content_type, 0) + 1

    # Calculate average quality score
    quality_scores = [item.get("quality_score", 0) for item in items if item.get("quality_score")]
    if quality_scores:
        stats["avg_quality_score"] = sum(quality_scores) / len(quality_scores)

    return stats
