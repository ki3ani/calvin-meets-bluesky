import json
import logging
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BedrockService:
    """Service for interacting with AWS Bedrock (Claude and Stability AI)"""

    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
        )
        self.claude_model = settings.BEDROCK_CLAUDE_MODEL
        self.stability_model = settings.BEDROCK_STABILITY_MODEL

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = None,
        temperature: float = None,
    ) -> Dict:
        """
        Generate text using Claude via AWS Bedrock.

        Args:
            prompt: The user prompt to send to Claude
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens to generate (defaults to config)
            temperature: Temperature for generation (defaults to config)

        Returns:
            Dict with 'content' (str) and 'usage' (dict) keys
        """
        try:
            max_tokens = max_tokens or settings.BEDROCK_MAX_TOKENS
            temperature = temperature if temperature is not None else settings.BEDROCK_TEMPERATURE

            # Build the request body for Claude 3
            messages = [{"role": "user", "content": prompt}]

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            # Add system prompt if provided
            if system_prompt:
                body["system"] = system_prompt

            logger.info(f"Sending request to Bedrock Claude model: {self.claude_model}")
            logger.debug(f"Request body: {json.dumps(body, indent=2)}")

            response = self.bedrock_runtime.invoke_model(
                modelId=self.claude_model,
                body=json.dumps(body),
            )

            response_body = json.loads(response.get("body").read())
            logger.debug(f"Response: {json.dumps(response_body, indent=2)}")

            # Extract the text content from Claude's response
            content = response_body.get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")
            else:
                text = ""

            return {
                "content": text,
                "usage": response_body.get("usage", {}),
                "stop_reason": response_body.get("stop_reason"),
            }

        except ClientError as e:
            logger.error(f"AWS Bedrock ClientError: {str(e)}")
            raise Exception(f"Failed to generate text with Bedrock: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    def generate_text_with_conversation(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = None,
        temperature: float = None,
    ) -> Dict:
        """
        Generate text using Claude with a multi-turn conversation.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation

        Returns:
            Dict with 'content' (str) and 'usage' (dict) keys
        """
        try:
            max_tokens = max_tokens or settings.BEDROCK_MAX_TOKENS
            temperature = temperature if temperature is not None else settings.BEDROCK_TEMPERATURE

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            if system_prompt:
                body["system"] = system_prompt

            logger.info(f"Sending conversation to Bedrock: {len(messages)} messages")

            response = self.bedrock_runtime.invoke_model(
                modelId=self.claude_model,
                body=json.dumps(body),
            )

            response_body = json.loads(response.get("body").read())

            content = response_body.get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")
            else:
                text = ""

            return {
                "content": text,
                "usage": response_body.get("usage", {}),
                "stop_reason": response_body.get("stop_reason"),
            }

        except Exception as e:
            logger.error(f"Error in conversation generation: {str(e)}")
            raise

    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        style_preset: str = "photographic",
        cfg_scale: float = 7.0,
        steps: int = 30,
    ) -> bytes:
        """
        Generate an image using Stability AI via AWS Bedrock.

        Args:
            prompt: The text prompt for image generation
            negative_prompt: What to avoid in the image
            style_preset: Style preset for the image
            cfg_scale: How strictly to follow the prompt (1-35)
            steps: Number of diffusion steps (10-50)

        Returns:
            bytes: The generated image data
        """
        try:
            body = {
                "text_prompts": [{"text": prompt, "weight": 1.0}],
                "cfg_scale": cfg_scale,
                "steps": steps,
                "seed": 0,
                "width": 1024,
                "height": 1024,
            }

            if negative_prompt:
                body["text_prompts"].append({"text": negative_prompt, "weight": -1.0})

            if style_preset:
                body["style_preset"] = style_preset

            logger.info(f"Generating image with Stability AI: {self.stability_model}")
            logger.info(f"Prompt: {prompt[:100]}...")

            response = self.bedrock_runtime.invoke_model(
                modelId=self.stability_model,
                body=json.dumps(body),
            )

            response_body = json.loads(response.get("body").read())

            # Stability AI returns base64 encoded images
            artifacts = response_body.get("artifacts", [])
            if artifacts and len(artifacts) > 0:
                import base64

                image_data = base64.b64decode(artifacts[0].get("base64"))
                logger.info("Successfully generated image")
                return image_data
            else:
                raise Exception("No image artifacts returned from Stability AI")

        except ClientError as e:
            logger.error(f"AWS Bedrock ClientError in image generation: {str(e)}")
            raise Exception(f"Failed to generate image with Bedrock: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            raise

    def evaluate_quality(self, content: str, content_type: str) -> Dict:
        """
        Use Claude to evaluate the quality of generated content.

        Args:
            content: The content to evaluate
            content_type: Type of content (philosophy, joke, story, etc.)

        Returns:
            Dict with 'score' (float 0-1) and 'feedback' (str) keys
        """
        try:
            evaluation_prompt = f"""You are a content quality evaluator. Rate the following {content_type} content on a scale of 0.0 to 1.0 based on:
- Originality and creativity
- Clarity and coherence
- Engagement and impact
- Appropriateness for social media

Content to evaluate:
{content}

Respond ONLY with a JSON object in this exact format:
{{"score": 0.85, "feedback": "Brief feedback here"}}

Do not include any other text or explanation."""

            response = self.generate_text(
                prompt=evaluation_prompt,
                temperature=0.3,  # Lower temperature for more consistent evaluation
                max_tokens=300,
            )

            # Parse the JSON response
            result = json.loads(response["content"])
            return {
                "score": float(result.get("score", 0.5)),
                "feedback": result.get("feedback", ""),
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quality evaluation JSON: {str(e)}")
            logger.error(f"Response was: {response.get('content', '')}")
            return {"score": 0.5, "feedback": "Failed to evaluate"}
        except Exception as e:
            logger.error(f"Error in quality evaluation: {str(e)}")
            return {"score": 0.5, "feedback": f"Error: {str(e)}"}
