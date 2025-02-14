import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_s3_storage():
    # Create a test file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = f"test_image_{timestamp}.txt"
    test_content = f"This is a test file content for S3 storage testing - {timestamp}"

    with open(test_file, "w") as f:
        f.write(test_content)

    try:
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.upload_file.return_value = None
        mock_s3.generate_presigned_url.return_value = "https://test-url.com"

        # Initialize storage service with mocked S3
        with patch("boto3.client", return_value=mock_s3):
            storage = StorageService()

            # Test file upload
            storage_path, access_url = await storage.save_file(test_file)

            assert storage_path is not None
            assert access_url is not None
            assert access_url.startswith("https://")

            # Test file deletion
            success = await storage.delete_file(storage_path)
            assert success is True

    finally:
        # Cleanup local test file
        if os.path.exists(test_file):
            os.remove(test_file)
