import os

import boto3
import magic
from botocore.exceptions import ClientError


class S3Service:
    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        region_name: str = None,
    ):
        self.bucket_name = bucket_name
        self.region_name = region_name or "us-east-1"
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=self.region_name,
        )

    def _get_object_key(self, object_name: str) -> str:
        """Extract the object key from a full path or S3 URI"""
        if object_name.startswith("s3://"):
            return object_name.split("/", 3)[-1]
        return object_name

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
