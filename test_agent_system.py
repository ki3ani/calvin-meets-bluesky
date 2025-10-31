"""
Test script for AI Agent System

This script helps you test the AI agent system locally before deploying to Lambda.
It tests each component individually and then runs a full workflow test.

Usage:
    python test_agent_system.py
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if all required environment variables are set"""
    logger.info("=" * 60)
    logger.info("Checking environment variables...")
    logger.info("=" * 60)

    required_vars = [
        "AWS_REGION",
        "BEDROCK_REGION",
        "S3_BUCKET_NAME",
        "DYNAMODB_CONTENT_TABLE",
        "BLUESKY_USERNAME",
        "BLUESKY_PASSWORD",
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            logger.error(f"❌ {var}: NOT SET")
        else:
            # Mask sensitive values
            display_value = value if "PASSWORD" not in var else "***"
            logger.info(f"✅ {var}: {display_value}")

    if missing:
        logger.error(f"\n❌ Missing environment variables: {', '.join(missing)}")
        logger.error("Please set them before running tests.")
        return False

    logger.info("✅ All environment variables set!\n")
    return True


def test_bedrock_service():
    """Test AWS Bedrock connectivity"""
    logger.info("=" * 60)
    logger.info("Testing AWS Bedrock Service...")
    logger.info("=" * 60)

    try:
        from app.services.bedrock_service import BedrockService

        bedrock = BedrockService()

        # Test simple text generation
        logger.info("Testing Claude text generation...")
        response = bedrock.generate_text(
            prompt="Say hello in one sentence.", max_tokens=50, temperature=0.5
        )

        content = response.get("content", "")
        logger.info(f"✅ Claude response: {content}")

        if len(content) > 0:
            logger.info("✅ Bedrock text generation working!\n")
            return True
        else:
            logger.error("❌ Bedrock returned empty response\n")
            return False

    except Exception as e:
        logger.error(f"❌ Bedrock test failed: {str(e)}\n")
        return False


def test_specialized_agents():
    """Test specialized content agents"""
    logger.info("=" * 60)
    logger.info("Testing Specialized Agents...")
    logger.info("=" * 60)

    from app.agents.specialized_agents import (
        PhilosopherAgent,
        ComedianAgent,
        StorytellerAgent,
        PoetAgent,
        WisdomAgent,
    )

    agents = [
        PhilosopherAgent(),
        ComedianAgent(),
        StorytellerAgent(),
        PoetAgent(),
        WisdomAgent(),
    ]

    all_passed = True

    for agent in agents:
        try:
            logger.info(f"\nTesting {agent.agent_name}...")
            result = agent.generate_content()

            content = result.get("text", "")
            logger.info(f"Generated content ({len(content)} chars):")
            logger.info(f"'{content[:100]}...'")

            if agent.validate_content(content):
                logger.info(f"✅ {agent.agent_name} working!")
            else:
                logger.error(f"❌ {agent.agent_name} validation failed")
                all_passed = False

        except Exception as e:
            logger.error(f"❌ {agent.agent_name} failed: {str(e)}")
            all_passed = False

    if all_passed:
        logger.info("\n✅ All agents working!\n")
    else:
        logger.error("\n❌ Some agents failed\n")

    return all_passed


def test_critic_agent():
    """Test the critic agent"""
    logger.info("=" * 60)
    logger.info("Testing Critic Agent...")
    logger.info("=" * 60)

    try:
        from app.agents.critic_agent import CriticAgent

        critic = CriticAgent()

        test_content = "Life is like a box of chocolates, you never know what you're gonna get."
        logger.info(f"Evaluating test content: '{test_content}'")

        evaluation = critic.evaluate_content(test_content, "wisdom")

        logger.info(f"Score: {evaluation['score']:.2f}")
        logger.info(f"Approved: {evaluation['approved']}")
        logger.info(f"Feedback: {evaluation['feedback']}")

        logger.info("✅ Critic agent working!\n")
        return True

    except Exception as e:
        logger.error(f"❌ Critic agent failed: {str(e)}\n")
        return False


def test_agent_orchestrator():
    """Test the full agent orchestration workflow"""
    logger.info("=" * 60)
    logger.info("Testing Agent Orchestrator (Full Workflow)...")
    logger.info("=" * 60)

    try:
        from app.agents.agent_orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()

        logger.info("Generating philosophy content...")
        result = orchestrator.generate_content(content_type="philosophy")

        if result.get("success"):
            logger.info(f"✅ Content generated successfully!")
            logger.info(f"Content ID: {result.get('content_id')}")
            logger.info(f"Quality Score: {result.get('quality_score'):.2f}")
            logger.info(f"Approved: {result.get('approved')}")
            logger.info(f"Attempts: {result.get('attempts')}")
            logger.info(f"\nContent:\n{result.get('content')}")
            logger.info("\n✅ Full workflow working!\n")
            return True
        else:
            logger.error(f"❌ Workflow failed: {result.get('error')}\n")
            return False

    except Exception as e:
        logger.error(f"❌ Orchestrator test failed: {str(e)}\n")
        return False


def test_content_scheduler():
    """Test the content scheduler service"""
    logger.info("=" * 60)
    logger.info("Testing Content Scheduler Service...")
    logger.info("=" * 60)

    try:
        from app.services.content_scheduler_service import ContentSchedulerService

        scheduler = ContentSchedulerService()

        logger.info("Generating batch content (3 pieces)...")
        result = scheduler.generate_new_content(count=3)

        generated = result.get("generated", 0)
        failed = result.get("failed", 0)

        logger.info(f"Generated: {generated}, Failed: {failed}")

        if generated > 0:
            logger.info("✅ Content scheduler working!\n")
            return True
        else:
            logger.error("❌ No content generated\n")
            return False

    except Exception as e:
        logger.error(f"❌ Scheduler test failed: {str(e)}\n")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AI AGENT SYSTEM TEST SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}\n")

    results = {}

    # Run tests
    results["Environment"] = check_environment()

    if not results["Environment"]:
        logger.error("\n❌ Environment check failed. Please fix and try again.")
        sys.exit(1)

    results["Bedrock Service"] = test_bedrock_service()
    results["Specialized Agents"] = test_specialized_agents()
    results["Critic Agent"] = test_critic_agent()
    results["Agent Orchestrator"] = test_agent_orchestrator()
    results["Content Scheduler"] = test_content_scheduler()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! System ready for deployment.\n")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix before deploying.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
