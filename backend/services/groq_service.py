import os
import json
import logging

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)

# List of models to try sequentially in case of rate limits
FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.3-70b-specdec",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "llama3-8b-8192",
]


class MissingAPIKeyError(Exception):
    pass


class GroqAPIError(Exception):
    pass


def generate_script(prompt: str):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise MissingAPIKeyError("GROQ_API_KEY is missing in .env")

    last_error = None
    for model in FALLBACK_MODELS:
        try:
            logger.info("Attempting script generation with Groq model: %s", model)
            client = Groq(api_key=api_key)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert YouTube educational script writer. "
                            "Return ONLY valid JSON. "
                            "Create an engaging educational video with a strong hook. "
                            "Explain concepts matching the exact complexity level, tone, and visual instructions specified in the user prompt. "
                            "Use smooth transitions between scenes. "
                            "End with a memorable conclusion. "
                            "Each scene must contain: scene_number, duration_seconds, visual_prompt, and voiceover."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.7,
            )

            content = response.choices[0].message.content

            # Remove markdown JSON formatting if the model adds it
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Verify it parses as JSON before returning
            json.loads(content)
            
            logger.info("Successfully generated script using model: %s", model)
            return content

        except json.JSONDecodeError as error:
            logger.error("Invalid JSON format from model %s: %s", model, error)
            last_error = GroqAPIError("Groq returned invalid JSON")
            continue
        except Exception as error:
            logger.warning("Groq model %s failed: %s. Retrying next model...", model, error)
            last_error = error
            continue

    logger.error("All Groq models failed. Last error: %s", last_error)
    raise GroqAPIError(str(last_error))


def generate_chat(
    messages: list[dict],
    response_format: dict | None = None,
    temperature: float = 0.7,
) -> str:
    """Generate a chat response from Groq using custom messages and settings."""
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise MissingAPIKeyError("GROQ_API_KEY is missing in .env")

    last_error = None
    for model in FALLBACK_MODELS:
        try:
            logger.info("Attempting chat generation with Groq model: %s", model)
            client = Groq(api_key=api_key)

            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            logger.info("Successfully completed chat generation using model: %s", model)
            return content.strip()

        except Exception as error:
            logger.warning("Groq model %s failed in generate_chat: %s. Retrying next model...", model, error)
            last_error = error
            continue

    logger.error("All Groq models failed in generate_chat. Last error: %s", last_error)
    raise GroqAPIError(str(last_error))