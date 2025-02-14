import asyncio
import os
import webbrowser
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from app.services.storage_service import StorageService

# Load environment variables from .env file
load_dotenv()


async def list_bucket_contents(s3_client, bucket_name):
    """List all files in the bucket"""
    try:
        print(f"\nListing contents of bucket: {bucket_name}")
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if "Contents" in response:
            print("\nFiles in bucket:")
            for obj in response["Contents"]:
                print(f"- {obj['Key']} (Size: {obj['Size']} bytes)")
        else:
            print("\nBucket is empty")
    except ClientError as e:
        print(f"Error listing bucket contents: {e}")


async def test_s3_storage():
    # Create a test file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = f"test_image_{timestamp}.txt"
    with open(test_file, "w") as f:
        f.write(f"This is a test file content for S3 storage testing - {timestamp}")

    try:
        # Initialize storage service
        storage = StorageService()

        # Initialize S3 client
        print("\nInitializing S3 client...")
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )

        # Upload file
        print(f"\n1. Uploading file: {test_file}")
        storage_path, access_url = await storage.save_file(test_file)

        if storage_path and access_url:
            print("\n✓ File uploaded successfully!")
            print(f"Storage path: {storage_path}")
            print(f"\nAccess URL (valid for 1 hour):")  # noqa
            print("=" * 80)
            print(access_url)
            print("=" * 80)

            # Try to open the URL in browser
            print("\nAttempting to open URL in your default browser...")
            webbrowser.open(access_url)

            # List bucket contents after upload
            await list_bucket_contents(s3_client, os.getenv("S3_BUCKET_NAME"))

            # Ask user if they want to delete the file
            user_input = input(
                "\nPress 'D' to delete the file or any other key to keep it: "
            )

            if user_input.upper() == "D":
                # Delete file
                print("\nDeleting file...")
                success = await storage.delete_file(storage_path)
                if success:
                    print("✓ File deletion succeeded")
                else:
                    print("✗ File deletion failed")

                # List bucket contents after deletion
                await list_bucket_contents(s3_client, os.getenv("S3_BUCKET_NAME"))
            else:
                print(
                    "\nFile will remain in the bucket. You can access it at the URL above for the next hour."  # noqa
                )
                print(
                    "To delete it later, you can run the script again and use the delete option."  # noqa
                )
        else:
            print("✗ File upload failed!")

    finally:
        # Cleanup local test file
        if os.path.exists(test_file):
            os.remove(test_file)


if __name__ == "__main__":
    asyncio.run(test_s3_storage())
