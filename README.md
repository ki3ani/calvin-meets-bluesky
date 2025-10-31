# **AI Creative Content Generator 🤖✨**

An intelligent, multi-agent AI system that generates creative content (philosophy, jokes, stories, poems, wisdom) using AWS Bedrock and posts to Bluesky. Powered by Claude 3.5 Sonnet and Stability AI.

## **What It Does 🚀**
- **🧠 Multi-Agent AI System** – Specialized agents for different content types with unique personalities
- **✍️ Creative Content Generation** – Philosophy, jokes, micro-stories, poetry, and wisdom
- **🎨 AI-Generated Images** – Optional visual content using Stability AI
- **⚖️ Quality Control** – CriticAgent evaluates and improves content before posting
- **📊 Smart Content Variety** – ContentDirector ensures diverse, balanced content
- **📢 Auto-Posts to Bluesky** – Scheduled posting with engagement-optimized formatting
- **🎯 AWS Serverless** – Fully serverless architecture with Lambda + EventBridge

## **How It Works 🔄**

### Multi-Agent Workflow
1. **ContentDirector** decides what type of content to create (ensures variety)
2. **Specialized Agent** generates content (Philosopher, Comedian, Storyteller, Poet, or Wisdom)
3. **CriticAgent** evaluates quality and provides feedback
4. **Agent revises** content if quality is below threshold (iterative improvement)
5. **ImageGenerator** creates complementary AI image (optional)
6. **Save to DynamoDB + S3** with quality scores and metadata
7. **Post to Bluesky** on schedule with best unposted content

### Agent Personalities

- **PhilosopherAgent** 💭 – Deep, contemplative, explores existence and meaning
- **ComedianAgent** 😄 – Sharp wit, observational humor, modern and relatable
- **StorytellerAgent** 📖 – Micro-fiction with twists, complete narratives
- **PoetAgent** ✨ – Evocative poetry, haikus, beautiful language
- **WisdomAgent** 🌟 – Practical life advice, inspirational insights

## **Tech Stack 🛠️**

### AI & ML
- **AWS Bedrock** – Claude 3.5 Sonnet for text generation
- **Stability AI** – Stable Diffusion XL for image generation

### Infrastructure
- **AWS Lambda** – Serverless content generation and posting
- **Amazon DynamoDB** – Content storage and metadata
- **Amazon S3** – Image and asset storage
- **EventBridge** – Scheduled triggers
- **Bluesky API** – Social media posting

### Python Libraries
- **boto3** – AWS SDK
- **langchain** – AI orchestration (optional enhancement)
- **pydantic** – Configuration management

## **Quick Start 🏃**

### Prerequisites
- AWS Account with Bedrock access
- Bluesky account
- Python 3.9+

### Setup

1. **Clone and install dependencies:**
```bash
git clone <repo-url>
cd calvin-meets-bluesky
pip install -r requirements.txt
```

2. **Enable AWS Bedrock models:**
   - Go to AWS Bedrock Console → Model Access
   - Request access to Claude 3.5 Sonnet and Stability AI

3. **Create DynamoDB table:**
```bash
aws dynamodb create-table \
    --table-name GeneratedContent \
    --attribute-definitions AttributeName=content_id,AttributeType=S \
    --key-schema AttributeName=content_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

4. **Set environment variables:**
```bash
export BEDROCK_REGION=us-east-1
export DYNAMODB_CONTENT_TABLE=GeneratedContent
export BLUESKY_USERNAME=your-username
export BLUESKY_PASSWORD=your-password
export S3_BUCKET_NAME=your-bucket
```

5. **Deploy to Lambda:**
```bash
./build_lambda.sh
# Upload to Lambda via AWS Console or CLI
```

6. **Configure EventBridge schedules** (see `AI_AGENT_SETUP.md`)

📖 **Full setup guide:** See [AI_AGENT_SETUP.md](./AI_AGENT_SETUP.md) for detailed instructions.

## **Usage Examples**

### Generate Content
```python
from app.services.content_scheduler_service import ContentSchedulerService

scheduler = ContentSchedulerService()

# Generate mixed content
result = scheduler.generate_new_content(count=5)

# Generate specific type
result = scheduler.generate_content_on_demand("philosophy")
```

### Test Lambda Functions
```bash
# Generate content
aws lambda invoke --function-name generate-content \
    --payload '{"count": 3}' response.json

# Create post
aws lambda invoke --function-name create-post \
    --payload '{}' response.json
```

## **Configuration ⚙️**

### Content Types
Customize in `app/config.py`:
```python
CONTENT_TYPES = ["philosophy", "joke", "story", "poem", "wisdom"]
```

### Quality Threshold
```python
MIN_QUALITY_SCORE = 0.7  # 0.0 to 1.0
```

### Image Generation
```bash
ENABLE_IMAGE_GENERATION=true  # or false
```

## **Architecture Diagram**

```
┌─────────────────┐
│  EventBridge    │
│   (Schedule)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Lambda: generate_content        │
│  ┌────────────────────────────────────┐ │
│  │     ContentDirector                │ │
│  │   (Decides content type)           │ │
│  └──────────────┬─────────────────────┘ │
│                 ▼                        │
│  ┌────────────────────────────────────┐ │
│  │  Specialized Agent                 │ │
│  │  (Philosopher/Comedian/etc)        │ │
│  └──────────────┬─────────────────────┘ │
│                 ▼                        │
│  ┌────────────────────────────────────┐ │
│  │      CriticAgent                   │ │
│  │  (Evaluates & provides feedback)   │ │
│  └──────────────┬─────────────────────┘ │
│                 ▼                        │
│  ┌────────────────────────────────────┐ │
│  │   ImageGenerator (optional)        │ │
│  └──────────────┬─────────────────────┘ │
└─────────────────┼─────────────────────────┘
                  ▼
         ┌────────────────┐
         │   DynamoDB     │
         │   + S3         │
         └────────┬───────┘
                  │
         ┌────────▼──────────┐
         │  Lambda:          │
         │  create_post      │
         └────────┬──────────┘
                  ▼
         ┌────────────────┐
         │   Bluesky      │
         └────────────────┘
```

## **Cost Estimates 💰**

Per 1000 content pieces with images:
- AWS Bedrock (Claude): ~$150
- AWS Bedrock (Stability AI): ~$40
- Lambda/DynamoDB/S3: ~$5
- **Total: ~$195 per 1000 posts**

Set up billing alerts! 🔔

## **Monitoring 📊**

### Key Metrics
- Content quality scores
- Content type distribution
- Post success rate
- Generation time

### CloudWatch Logs
```bash
aws logs tail /aws/lambda/generate-content --follow
```

## **Customization Ideas 💡**

1. **Add new agent types** – Create agents for different content styles
2. **Adjust personalities** – Modify prompts in `specialized_agents.py`
3. **Custom image styles** – Change style presets in `image_generator.py`
4. **Multi-platform posting** – Add Twitter, Mastodon, etc.
5. **Engagement learning** – Use feedback to improve future content
6. **Themed content** – Generate content around specific topics

## **Troubleshooting 🔧**

See [AI_AGENT_SETUP.md](./AI_AGENT_SETUP.md) for detailed troubleshooting guide.

Common issues:
- **Bedrock access denied** → Enable model access in AWS Console
- **Low quality scores** → Adjust `MIN_QUALITY_SCORE` or agent prompts
- **Timeout errors** → Increase Lambda timeout to 5 minutes

## **Contributing 🤝**

Ideas for improvements:
- [ ] Add engagement tracking and learning
- [ ] Implement A/B testing for content styles
- [ ] Add more content types
- [ ] Multi-language support
- [ ] Content scheduling optimization

## **License**

MIT License - Feel free to fork and customize!

---

**From comic bot to AI creative studio!** 🎨🤖

Built with ❤️ using AWS Bedrock, Claude, and creative AI agents.

