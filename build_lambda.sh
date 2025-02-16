#!/bin/bash
set -e

# Remove any previous package directory and ZIP file
rm -rf lambda-package calvin-bot.zip
mkdir -p lambda-package

# Build the package using the AWS Lambda Python 3.11 image in Docker
docker run --rm -v "$PWD":/var/task --entrypoint bash public.ecr.aws/lambda/python:3.11 -c "
    set -e;
    echo 'Installing dependencies...';
    pip install -r requirements.txt -t /var/task/lambda-package;
    echo 'Copying application code...';
    cp -r app /var/task/lambda-package/;
    echo 'Build complete.';
"

# Create the ZIP file from the lambda-package directory
cd lambda-package
zip -r ../calvin-bot.zip .
cd ..

echo "Lambda package created: calvin-bot.zip"

# Upload the ZIP file to your S3 bucket
echo "Uploading calvin-bot.zip to S3..."
aws s3 cp calvin-bot.zip s3://calvobit/lambda/calvin-bot.zip || { echo "Failed to upload ZIP to S3"; exit 1; }


echo "Lambda package is now available at: s3://calvobit/lambda/calvin-bot.zip"
