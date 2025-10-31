# AI Creative Content Generator - Setup Guide

## Overview

This project has been transformed from a comic scraping bot into a sophisticated **AI Agentic Workflow System** that generates creative content using AWS Bedrock (Claude & Stability AI) and posts to Bluesky.

## Architecture

### Multi-Agent System
- **ContentDirector**: Decides what type of content to create based on variety and balance
- **Specialized Creator Agents**:
  - `PhilosopherAgent`: Deep philosophical musings
  - `ComedianAgent`: Witty jokes and observations
  - `StorytellerAgent`: Micro-stories and flash fiction
  - `PoetAgent`: Poetry and poetic observations
  - `WisdomAgent`: Inspirational wisdom and life advice
- **CriticAgent**: Evaluates content quality and provides feedback
- **ImageGenerator**: Creates AI-generated images to accompany content
- **AgentOrchestrator**: Coordinates the entire workflow

### Workflow
```
EventBridge Trigger
    ↓
Lambda: generate_content
    ↓
ContentDirector (decides content type)
    ↓
Specialized Agent (generates content)
    ↓
CriticAgent (evaluates & provides feedback)
    ↓
Agent revises if needed
    ↓
ImageGenerator (optional)
    ↓
Save to DynamoDB + S3
    ↓
Lambda: create_post
    ↓
Post to Bluesky
```

## AWS Setup Requirements

### 1. AWS Bedrock Access

You need access to AWS Bedrock models:

```bash
# Enable model access in AWS Console:
# AWS Bedrock → Model Access → Request Access

# Required models:
# - Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet-20241022-v2:0)
# - Stable Diffusion XL (stability.stable-diffusion-xl-v1)
```

### 2. IAM Permissions

Update your Lambda execution role with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        "arn:aws:bedrock:*::foundation-model/stability.stable-diffusion-xl-v1"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/Comics",
        "arn:aws:dynamodb:*:*:table/GeneratedContent"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

### 3. DynamoDB Tables

Create a new DynamoDB table for generated content:

```bash
aws dynamodb create-table \
    --table-name GeneratedContent \
    --attribute-definitions AttributeName=content_id,AttributeType=S \
    --key-schema AttributeName=content_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

### 4. Environment Variables

Update your Lambda environment variables:

```bash
# Required
BEDROCK_REGION=us-east-1
BEDROCK_CLAUDE_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_STABILITY_MODEL=stability.stable-diffusion-xl-v1
DYNAMODB_CONTENT_TABLE=GeneratedContent

# Optional
BEDROCK_MAX_TOKENS=2000
BEDROCK_TEMPERATURE=1.0
ENABLE_IMAGE_GENERATION=true
MIN_QUALITY_SCORE=0.7

# Existing vars (keep these)
DYNAMODB_TABLE=Comics
S3_BUCKET_NAME=your-bucket-name
BLUESKY_USERNAME=your-username
BLUESKY_PASSWORD=your-password
AWS_REGION=us-east-1
```

## Deployment

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Build Lambda Package

```bash
./build_lambda.sh
```

### 3. Deploy to Lambda

```bash
# Update your Lambda function
aws lambda update-function-code \
    --function-name your-function-name \
    --zip-file fileb://lambda_package.zip

# Or use your existing deployment method
```

### 4. Update Lambda Handlers

Update your Lambda function configurations:

**Content Generation Lambda:**
- Handler: `app.lambda_handler.generate_content`
- Timeout: 5 minutes (AI generation can take time)
- Memory: 512 MB or higher

**Post Creation Lambda:**
- Handler: `app.lambda_handler.create_post`
- Timeout: 2 minutes
- Memory: 256 MB

**Statistics Lambda (optional):**
- Handler: `app.lambda_handler.get_stats`
- Timeout: 30 seconds
- Memory: 256 MB

### 5. Update EventBridge Rules

Update your EventBridge schedules:

```bash
# Content generation - run 3x per day
aws events put-rule \
    --name generate-content-schedule \
    --schedule-expression "cron(0 8,14,20 * * ? *)"

# Post creation - run 2x per day
aws events put-rule \
    --name create-post-schedule \
    --schedule-expression "cron(0 10,18 * * ? *)"
```

## Testing

### Test Content Generation Locally

```python
from app.services.content_scheduler_service import ContentSchedulerService

scheduler = ContentSchedulerService()

# Generate 3 pieces of content
result = scheduler.generate_new_content(count=3)
print(result)

# Generate specific type
result = scheduler.generate_content_on_demand("philosophy")
print(result)
```

### Test Lambda Functions

```bash
# Test content generation
aws lambda invoke \
    --function-name your-function-name \
    --payload '{"count": 3}' \
    response.json

# Test with specific content type
aws lambda invoke \
    --function-name your-function-name \
    --payload '{"count": 1, "content_type": "joke"}' \
    response.json

# Test post creation
aws lambda invoke \
    --function-name your-post-function-name \
    --payload '{}' \
    response.json
```

## Monitoring

### CloudWatch Metrics

Monitor these key metrics:
- Lambda invocation count and errors
- Lambda duration (watch for timeouts)
- DynamoDB read/write capacity
- Bedrock API errors

### CloudWatch Logs

Key log groups:
- `/aws/lambda/your-generate-content-function`
- `/aws/lambda/your-create-post-function`

Search for:
- `"ContentDirector decided"` - See what content types are being selected
- `"Quality score"` - Monitor content quality
- `"Successfully posted"` - Confirm posts are working

## Cost Considerations

### Estimated Costs (per 1000 content generations)

**AWS Bedrock:**
- Claude 3.5 Sonnet: ~$0.15 per content piece (varies by length)
- Stability AI: ~$0.04 per image
- Total per content with image: ~$0.19

**Other AWS Services:**
- Lambda: Minimal ($0.01-0.05)
- DynamoDB: Minimal with on-demand pricing
- S3: Storage costs only

**Recommended Budget:** Set up billing alerts for Bedrock usage

## Content Types

The system generates 5 types of content:

1. **Philosophy** - Deep thoughts, existential musings
2. **Jokes** - Witty observations, humor
3. **Stories** - Micro-fiction, flash fiction
4. **Poems** - Poetry, haikus, verse
5. **Wisdom** - Life advice, inspirational thoughts

## Customization

### Adjust Content Types

Edit `app/config.py`:

```python
CONTENT_TYPES: list = ["philosophy", "joke", "story", "poem", "wisdom"]
```

### Modify Agent Prompts

Edit agent files in `app/agents/specialized_agents.py` to change personalities and styles.

### Adjust Quality Threshold

Edit `app/config.py`:

```python
MIN_QUALITY_SCORE: float = 0.7  # Lower = more lenient, Higher = stricter
```

### Enable/Disable Image Generation

```bash
# In Lambda environment variables
ENABLE_IMAGE_GENERATION=false  # Set to false to disable
```

## Troubleshooting

### "Access Denied" for Bedrock

- Check IAM permissions
- Ensure model access is enabled in Bedrock console
- Verify region matches (us-east-1)

### Content Not Generated

- Check CloudWatch logs for errors
- Verify environment variables are set
- Test Bedrock connectivity

### Posts Not Created

- Check Bluesky credentials
- Verify DynamoDB has unposted content
- Check Lambda timeout settings

### Low Quality Scores

- Adjust `MIN_QUALITY_SCORE` setting
- Review agent prompts
- Check critic agent feedback in logs

## Next Steps

1. Monitor the first few generations closely
2. Adjust quality thresholds based on results
3. Customize agent personalities as desired
4. Set up billing alerts for Bedrock usage
5. Review and refine based on audience engagement

## Support

For issues or questions:
- Check CloudWatch logs first
- Review IAM permissions
- Verify Bedrock model access
- Test each component individually

Enjoy your AI creative content bot! 🤖✨
