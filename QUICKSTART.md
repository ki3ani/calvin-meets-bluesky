# Quick Start Guide

Get your AI Creative Content Generator running in 15 minutes!

## Step 1: AWS Bedrock Setup (5 min)

1. Go to AWS Console → Bedrock → Model Access
2. Request access to:
   - `anthropic.claude-3-5-sonnet-20241022-v2:0`
   - `stability.stable-diffusion-xl-v1`
3. Wait for approval (usually instant)

## Step 2: Create DynamoDB Table (2 min)

```bash
aws dynamodb create-table \
    --table-name GeneratedContent \
    --attribute-definitions AttributeName=content_id,AttributeType=S \
    --key-schema AttributeName=content_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

## Step 3: Set Environment Variables (2 min)

Create `.env` file (for local testing):

```bash
# AWS Settings
AWS_REGION=us-east-1
BEDROCK_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# DynamoDB
DYNAMODB_CONTENT_TABLE=GeneratedContent
DYNAMODB_TABLE=Comics

# Bluesky
BLUESKY_USERNAME=your-username.bsky.social
BLUESKY_PASSWORD=your-app-password

# Optional
ENABLE_IMAGE_GENERATION=true
MIN_QUALITY_SCORE=0.7
```

## Step 4: Test Locally (5 min)

```bash
# Install dependencies
pip install -r requirements.txt

# Run test suite
python test_agent_system.py
```

## Step 5: Deploy to Lambda (3 min)

```bash
# Build package
./build_lambda.sh

# Upload to Lambda (use AWS Console or CLI)
aws lambda update-function-code \
    --function-name your-function-name \
    --zip-file fileb://lambda_package.zip
```

## Step 6: Test Lambda

```bash
# Test content generation
aws lambda invoke \
    --function-name your-generate-function \
    --payload '{"count": 2}' \
    output.json

cat output.json
```

## What Happens Next?

1. **EventBridge triggers** `generate_content` Lambda (3x/day)
2. **AI agents create** philosophical thoughts, jokes, stories, poems, wisdom
3. **Quality control** ensures only good content is saved
4. **EventBridge triggers** `create_post` Lambda (2x/day)
5. **Best content** is posted to Bluesky automatically

## Monitor Your Bot

```bash
# View logs
aws logs tail /aws/lambda/your-function-name --follow

# Get statistics
aws lambda invoke \
    --function-name your-function-name \
    --handler app.lambda_handler.get_stats \
    --payload '{}' \
    stats.json
```

## Customize

Edit `app/agents/specialized_agents.py` to adjust:
- Agent personalities
- Content styles
- Tone and voice

Edit `app/config.py` to adjust:
- Content types
- Quality thresholds
- Image generation settings

## Troubleshooting

**"AccessDeniedException" for Bedrock:**
→ Enable model access in AWS Bedrock console

**"No module named 'app'":**
→ Run `pip install -r requirements.txt`

**"Table not found":**
→ Create DynamoDB tables (see Step 2)

**Content quality too low:**
→ Lower `MIN_QUALITY_SCORE` in config or adjust agent prompts

## Cost Management

Set up billing alerts:

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name bedrock-costs \
    --alarm-description "Alert if Bedrock costs exceed $50" \
    --metric-name EstimatedCharges \
    --namespace AWS/Billing \
    --statistic Maximum \
    --period 86400 \
    --evaluation-periods 1 \
    --threshold 50 \
    --comparison-operator GreaterThanThreshold
```

## Next Steps

1. ✅ Test locally with `test_agent_system.py`
2. ✅ Deploy to Lambda
3. ✅ Set up EventBridge schedules
4. ✅ Monitor first few posts
5. ✅ Adjust personalities and quality thresholds
6. 🎉 Enjoy automated creative content!

---

**Need help?** Check [AI_AGENT_SETUP.md](./AI_AGENT_SETUP.md) for detailed guide.
