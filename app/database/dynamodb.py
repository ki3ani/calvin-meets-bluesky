import os

import boto3
from boto3.dynamodb.conditions import Attr

DYNAMODB_REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "Comics")

dynamodb = boto3.resource("dynamodb", region_name=DYNAMODB_REGION)
table = dynamodb.Table(TABLE_NAME)


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
