"""OpenAI integration for educational script generation."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import APIError, OpenAI

from services.scene_converter import DURATION_SECONDS, SCENE_TARGETS
from services.section_builders import AUDIENCE_STYLE, DURATION_BLUEPRINTS

logger = logging.getLogger(__name__)

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

OPENAI_SCRIPT_MODEL = os.getenv("OPENAI_SCRIPT_MODEL", "gpt-4o-mini")

AUDIENCE_LABELS = {
    "school": "School students",
    "ug": "Undergraduate (UG) students",
    "pg": "Postgraduate (PG) students",
}

LANGUAGE_LABELS = {
    "english": "English",
    "hindi": "Hindi",
    "telugu": "Telugu",
}

DURATION_GUIDANCE = {
    "1": {
        "label": "1 minute",
        "scene_count": SCENE_TARGETS["1"],
        "total_seconds": DURATION_SECONDS["1"],
        "style": "fast pacing with a strong hook in the first scene",
        "structure": "introduction, main idea, summary",
    },
    "3": {
        "label": "3 minutes",
        "scene_count": SCENE_TARGETS["3"],
        "total_seconds": DURATION_SECONDS["3"],
        "style": "educational storytelling structure",
        "structure": "explanation, example, summary",
    },
    "5": {
        "label": "5 minutes",
        "scene_count": SCENE_TARGETS["5"],
        "total_seconds": DURATION_SECONDS["5"],
        "style": "detailed lesson with clear teaching progression",
        "structure": "introduction, definition, concepts, examples, applications, summary",
    },
    "10": {
        "label": "10 minutes",
        "scene_count": SCENE_TARGETS["10"],
        "total_seconds": DURATION_SECONDS["10"],
        "style": "documentary-style lecture",
        "structure": (
            "introduction, background, detailed explanation, examples, "
            "step-by-step process, real-world applications, quiz questions, conclusion"
        ),
    },
}


class MissingAPIKeyError(Exception):
    """Raised when OPENAI_API_KEY is not configured."""


class OpenAIAPIError(Exception):
    """Raised when the OpenAI API call fails."""


def get_openai_client() -> OpenAI:
    """Create an OpenAI client using the configured API key."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise MissingAPIKeyError(
            "OPENAI_API_KEY is missing. Add it to backend/.env and restart the server."
        )
    return OpenAI(api_key=api_key)


def build_openai_prompt(
    topic: str,
    audience: str,
    duration: str,
    language: str,
    duration_label: str,
    retry: bool = False,
) -> str:
    """Build a duration-aware prompt for structured scene generation."""
    guidance = DURATION_GUIDANCE.get(duration, DURATION_GUIDANCE["3"])
    audience_style = AUDIENCE_STYLE.get(audience, AUDIENCE_STYLE["school"])
    blueprint = DURATION_BLUEPRINTS.get(duration, DURATION_BLUEPRINTS["3"])
    section_titles = ", ".join(title for _, title in blueprint)

    retry_note = (
        "Return only valid JSON matching the schema exactly. "
        "Do not include markdown fences or commentary."
        if retry
        else ""
    )

    return f"""
Create an educational video script as structured JSON.

Topic: {topic}
Audience: {AUDIENCE_LABELS.get(audience, audience)}
Language: {LANGUAGE_LABELS.get(language, language)}
Video duration: {duration_label}
Teaching style: {audience_style["voice"]}
Complexity: {audience_style["complexity"]}

Duration requirements:
- Generate exactly {guidance["scene_count"]} scenes
- Total scene duration must equal {guidance["total_seconds"]} seconds
- Pacing: {guidance["style"]}
- Lesson structure: {guidance["structure"]}
- Section flow to cover: {section_titles}

Rules:
- Make every voiceover and visual prompt specific to "{topic}"
- Do not use generic filler sentences
- Voiceover text is spoken narration for the audience level and language
- Visual prompts describe what should appear on screen for AI image generation
- Scene numbers must start at 1 and increment by 1
- Each scene must include scene_number, duration_seconds, visual_prompt, voiceover

Return JSON with this shape:
{{
  "title": "Educational Video: {topic}",
  "duration": "{duration_label}",
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 10,
      "visual_prompt": "...",
      "voiceover": "..."
    }}
  ]
}}

{retry_note}
""".strip()


def generate_script_with_openai(
    topic: str,
    audience: str,
    duration: str,
    language: str,
    duration_label: str,
    retry: bool = False,
) -> str:
    """Call OpenAI chat completions and return raw JSON text for the structured script."""
    client = get_openai_client()
    prompt = build_openai_prompt(
        topic=topic,
        audience=audience,
        duration=duration,
        language=language,
        duration_label=duration_label,
        retry=retry,
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_SCRIPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert educational video script writer. "
                        "Respond with valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
    except APIError as error:
        logger.exception("OpenAI API request failed")
        raise OpenAIAPIError(f"OpenAI API request failed: {error}") from error
    except Exception as error:
        logger.exception("Unexpected OpenAI client error")
        raise OpenAIAPIError(f"OpenAI request failed: {error}") from error

    raw_text = (response.choices[0].message.content or "").strip()
    if not raw_text:
        raise OpenAIAPIError("OpenAI returned an empty response.")

    logger.info(
        "OpenAI script generated for topic=%r duration=%s scenes_requested=%s",
        topic,
        duration,
        DURATION_GUIDANCE.get(duration, DURATION_GUIDANCE["3"])["scene_count"],
    )
    return raw_text
