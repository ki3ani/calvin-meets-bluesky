import os
from typing import Optional

import boto3
import magic
from botocore.exceptions import ClientError


class S3Service:
    def __init__(
        self,
        bucket_name: str,
        region_name: str = None,
    ):
        self.bucket_name = bucket_name
        self.region_name = region_name or "us-east-1"

        # Let boto3 use IAM role by not providing credentials
        self.s3_client = boto3.client("s3", region_name=self.region_name)

        # Debug IAM role
        try:
            sts = boto3.client("sts")
            identity = sts.get_caller_identity()
            print(f"Using IAM identity: {identity['Arn']}")
        except Exception as e:
            print(f"Error getting IAM identity: {e}")

    def _get_object_key(self, object_name: str) -> str:
        """Extract the object key from a full path or S3 URI"""
        if object_name.startswith("s3://"):
            return object_name.split("/", 3)[-1]
        return object_name

    def get_file_content(self, object_name: str) -> Optional[bytes]:
        """Get the content of a file from S3"""
        try:
            object_key = self._get_object_key(object_name)
            print(f"Getting file content from S3: {self.bucket_name}/{object_key}")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=object_key
            )
            return response["Body"].read()
        except ClientError as e:
            print(f"Error getting file content from S3: {e}")
            return None

    def upload_file(self, file_path: str, object_name: str = None) -> bool:
        """Upload a file to S3 bucket"""
        if not object_name:
            object_name = os.path.basename(file_path)

        print(f"Uploading file {file_path} to {self.bucket_name}/{object_name}")

        # Determine content type
        mime = magic.Magic(mime=True)
        content_type = mime.from_file(file_path)
        print(f"Detected content type: {content_type}")

        try:
            with open(file_path, "rb") as file:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=file.read(),
                    ContentType=content_type,
                    CacheControl="max-age=31536000",  # 1 year cache
                )

            # Verify upload
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=object_name)
                print(f"✓ Verified file exists in S3: {object_name}")
                return True
            except ClientError:
                print(f"✗ File upload verification failed for: {object_name}")
                return False

        except ClientError as e:
            print(f"Error uploading file to S3: {e}")
            return False

    def get_file_url(self, object_name: str, expires_in: int = 3600) -> str:
        """Get a pre-signed URL for a file in S3"""
        try:
            object_key = self._get_object_key(object_name)
            print(f"Generating URL for {self.bucket_name}/{object_key}")

            # First verify the object exists
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            except ClientError:
                print(f"✗ File does not exist in S3: {object_key}")
                return None

            # Generate a URL that's valid for 1 hour by default
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expires_in,  # URL expiration time in seconds
            )
            print(
                f"✓ Generated pre-signed URL for {object_key} (valid for {expires_in/3600:.1f} hours)"  # noqa
            )
            return url
        except Exception as e:
            print(f"Error generating pre-signed URL: {e}")
            return None

    def save_content_to_file(self, content: bytes, object_name: str) -> bool:
        """Save content directly to S3"""
        try:
            # Determine content type from content
            mime = magic.Magic(mime=True)
            content_type = mime.from_buffer(content)

            print(f"Saving content to S3: {self.bucket_name}/{object_name}")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=content,
                ContentType=content_type,
                CacheControl="max-age=31536000",  # 1 year cache
            )
            return True
        except ClientError as e:
            print(f"Error saving content to S3: {e}")
            return False

    def delete_file(self, object_name: str) -> bool:
        """Delete a file from S3 bucket"""
        try:
            object_key = self._get_object_key(object_name)
            print(f"Deleting {self.bucket_name}/{object_key}")

            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)

            # Verify deletion
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
                print(f"✗ File still exists after deletion: {object_key}")
                return False
            except ClientError:
                print(f"✓ Verified file deletion: {object_key}")
                return True

        except ClientError as e:
            print(f"Error deleting file from S3: {e}")
            return False

    def get_permanent_file_url(self, object_name: str) -> str:
        """Get the permanent S3 URL (for database storage)"""
        return f"s3://{self.bucket_name}/{object_name}"
