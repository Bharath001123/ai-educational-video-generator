"""Visual planning and scene grouping service.

Coordinates the visual planning step to group related scenes, define a cohesive
visual style, generate fewer topic-relevant images, and reuse them across narration scenes.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from services.groq_service import generate_chat
from services.script_service import get_audience_profile
from services.image_service import generate_scene_image, retrieve_real_image

logger = logging.getLogger(__name__)


def plan_and_attach_visuals(
    scenes: list[dict[str, Any]],
    topic: str,
    audience: str,
    duration: str,
) -> list[dict[str, Any]]:
    """Plan topic-relevant images dynamically based on visual decision rules and educational accuracy."""
    if not scenes:
        return scenes

    profile = get_audience_profile(audience)

    # Summarize scenes for the LLM
    scenes_summary = []
    for s in scenes:
        scenes_summary.append({
            "scene_number": s.get("scene_number"),
            "voiceover": s.get("voiceover", ""),
            "original_visual_prompt": s.get("visual_prompt", "")
        })

    prompt = f"""
You are an expert visual planner and storyboard director for educational documentaries.
Your task is to analyze the narration scenes of an educational script and perform visual planning.

Topic: {topic}
Audience Level: {profile["label"]}
Visual Presentation Style Rules: {profile["visual_prompt_style"]}

Here are the narration scenes of the video:
{json.dumps(scenes_summary, indent=2)}

Core Directives for Visual Planning:
1. **Dynamic Visual Decisions**: Decide the required number of images dynamically. Image accuracy and topic relevance are more important than reducing the image count.
2. **Strict Reuse Rule**: Apply the check: "Can the current image explain this scene's narration?" 
   - If YES, reuse the existing image across multiple scenes.
   - If NO (i.e. the concept, process, object, or mechanism changes significantly), plan a new image.
   - Do not generate new images for minor narrative transitions or introductory/concluding filler sentences.
3. **Structured Prompt Format**: For each unique visual scene you plan, the `image_prompt` MUST be formatted EXACTLY as follows. Keep this exact label-based structure:
   Topic: {topic}
   Concept: [Define the specific educational concept being explained]
   Required visual: [Describe the exact objects, subjects, environment, or scientific/historical process that should appear. Ensure it is scientifically/historically accurate, has a clear main subject, and uses a 16:9 widescreen composition]
   Purpose: Help viewers understand the concept visually.
   Style: Educational documentary / realistic / cinematic, matching the overall style description, containing no random elements, no text, labels, watermarks, or unnecessary decorations.
4. **Avoid Generic Images**: Do not plan generic technology backgrounds, generic landscapes, stock photos of random people holding devices, or unrelated decorative illustrations. Every visual must directly explain the specific lesson of "{topic}".
5. **Cohesive Theme**: Define a single, cohesive `style_description` that outlines the art medium, color palette, lighting, background style, and tone to ensure visual consistency across all generated images. This style must match the "Visual Presentation Style Rules" above.
6. **Mapping**: Map every narration scene number (from 1 to {len(scenes)}) to exactly one of your planned visual scenes.
7. **Visual Source Decision**: For each visual scene, decide whether it is best explained by a real educational image/diagram or by an AI-generated image.
   - Set `visual_source` to `"real"` if the scene depicts:
     * Historical events, figures, landmarks, or artifacts
     * Geography, landforms, maps, or real-world locations
     * Anatomy, organs, cells, tissues, or biological structures
     * Scientific diagrams, chemical structures, physical equations, math models, or data plots
     * Classic educational illustrations, vintage/textbook diagrams, or schematics
   - Set `visual_source` to `"ai"` if the scene depicts:
     * Abstract concepts, feelings, futuristic visions, metaphors, or fictional concepts
     * Scenarios where no standard real-world picture or scientific diagram exists
   - For every scene where `visual_source` is `"real"`, you must provide a `"search_query"`. The `"search_query"` must be a precise, descriptive, search-engine-friendly query of 2 to 5 words (e.g., `"Abraham Lincoln photograph"`, `"mitosis diagram"`, `"Grand Canyon view"`, `"human skeletal system layout"`, `"water cycle schematic"`). Keep it in English and avoid search operators or punctuation.

Output the result in the following JSON format:
{{
  "style_description": "Cohesive style details here...",
  "visual_scenes": [
    {{
      "visual_id": 1,
      "visual_source": "real",
      "search_query": "Abraham Lincoln portrait",
      "image_prompt": "Topic: {topic}\\nConcept: ...\\nRequired visual: ...\\nPurpose: Help viewers understand the concept visually.\\nStyle: Educational documentary / realistic / cinematic, 16:9 composition, no text, no watermark",
      "scene_numbers": [1, 2]
    }}
  ]
}}
"""

    messages = [
        {
            "role": "system",
            "content": "You are a professional educational video director. You must return valid JSON only."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    plan = None
    try:
        logger.info("Calling Groq to plan visuals for topic: %s", topic)
        raw_response = generate_chat(messages, response_format={"type": "json_object"}, temperature=0.2)
        
        # Clean and parse JSON
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        
        plan = json.loads(cleaned)
        logger.info("Successfully planned visuals. Style description: %s", plan.get("style_description"))
    except Exception as e:
        logger.error("Failed to plan visuals via LLM: %s. Using fallback visual mapping.", e)
        plan = create_fallback_visual_plan(scenes, topic, profile)

    # If parsing succeeded but the structure is missing essential keys
    if not plan or "visual_scenes" not in plan:
        logger.warning("Invalid plan structure from LLM. Falling back to local grouping.")
        plan = create_fallback_visual_plan(scenes, topic, profile)

    # Generate or search images and map to narration scenes
    style_description = plan.get("style_description", "")
    planned_visuals = plan.get("visual_scenes", [])

    scene_image_urls: dict[int, str] = {}
    scene_prompts: dict[int, str] = {}
    scene_sources: dict[int, str] = {}
    scene_search_queries: dict[int, str] = {}
    generated_images: dict[int, tuple[str, str, str]] = {}  # v_id -> (url, source, search_query)

    for v_scene in planned_visuals:
        v_id = v_scene.get("visual_id")
        img_prompt = v_scene.get("image_prompt", "")
        scene_nums = v_scene.get("scene_numbers", [])
        visual_source = v_scene.get("visual_source", "ai")
        search_query = v_scene.get("search_query", "")

        if not scene_nums:
            continue

        # Combine specific image prompt with general style description if style is not already in prompt
        full_prompt = img_prompt
        if style_description and "style_description" not in img_prompt.lower():
            full_prompt = f"{img_prompt}\nOverall Style Reference: {style_description}"

        # Clean newlines for Pollinations AI router to prevent 404
        clean_prompt = full_prompt.replace("\n", " ").strip()
        clean_prompt = re.sub(r"\s+", " ", clean_prompt)

        # Generate or retrieve image once per visual_id
        if v_id not in generated_images:
            image_url = None
            actual_source = "ai"

            if visual_source == "real" and search_query:
                logger.info("Attempting to search and retrieve real image for query: %s", search_query)
                image_url = retrieve_real_image(search_query, scene_number=v_id)
                if image_url:
                    actual_source = "real"
                    logger.info("Successfully retrieved real image for visual scene %s from query: %s", v_id, search_query)
                else:
                    logger.warning("Failed to retrieve real image for query: %s. Falling back to AI image generation.", search_query)

            if not image_url:
                logger.info("Generating AI image for visual scene %s with prompt: %s", v_id, clean_prompt[:100])
                image_url = generate_scene_image(clean_prompt, scene_number=v_id)
                actual_source = "ai"

            generated_images[v_id] = (image_url, actual_source, search_query)
        else:
            image_url, actual_source, search_query = generated_images[v_id]

        for s_num in scene_nums:
            scene_image_urls[s_num] = image_url
            scene_prompts[s_num] = full_prompt
            scene_sources[s_num] = actual_source
            scene_search_queries[s_num] = search_query

    # Ensure every scene has a valid image and prompt mapped (post-pass correction)
    last_valid_url = None
    last_valid_prompt = None
    last_valid_source = "ai"
    last_valid_query = ""
    enriched_scenes: list[dict[str, Any]] = []

    for s in scenes:
        s_num = s.get("scene_number")
        if s_num in scene_image_urls:
            last_valid_url = scene_image_urls[s_num]
            last_valid_prompt = scene_prompts[s_num]
            last_valid_source = scene_sources[s_num]
            last_valid_query = scene_search_queries[s_num]
        else:
            if last_valid_url:
                logger.warning("Scene %s was omitted from visual planning. Reusing last scene image.", s_num)
                scene_image_urls[s_num] = last_valid_url
                scene_prompts[s_num] = last_valid_prompt
                scene_sources[s_num] = last_valid_source
                scene_search_queries[s_num] = last_valid_query
            else:
                first_item = next(iter(generated_images.values())) if generated_images else None
                if first_item:
                    first_url, first_source, first_query = first_item
                    logger.warning("Scene %s was omitted. Reusing first planned image.", s_num)
                    scene_image_urls[s_num] = first_url
                    scene_prompts[s_num] = f"Educational illustration of {topic}."
                    scene_sources[s_num] = first_source
                    scene_search_queries[s_num] = first_query
                else:
                    logger.warning("Generating fallback image for omitted scene %s", s_num)
                    fallback_prompt = (
                        f"Topic: {topic}\n"
                        f"Concept: Introduction to {topic}\n"
                        f"Required visual: An educational diagram representing {topic}\n"
                        f"Purpose: Help viewers understand the concept visually.\n"
                        f"Style: Educational documentary / realistic / cinematic, 16:9 composition"
                    )
                    clean_fallback_prompt = fallback_prompt.replace("\n", " ").strip()
                    clean_fallback_prompt = re.sub(r"\s+", " ", clean_fallback_prompt)
                    image_url = generate_scene_image(clean_fallback_prompt, scene_number=s_num)
                    scene_image_urls[s_num] = image_url
                    scene_prompts[s_num] = fallback_prompt
                    scene_sources[s_num] = "ai"
                    scene_search_queries[s_num] = ""
                    last_valid_url = image_url
                    last_valid_prompt = fallback_prompt
                    last_valid_source = "ai"
                    last_valid_query = ""

        enriched_scenes.append({
            **s,
            "image_url": scene_image_urls[s_num],
            "visual_prompt": scene_prompts[s_num],
            "visual_source": scene_sources[s_num],
            "search_query": scene_search_queries[s_num]
        })

    return enriched_scenes


def create_fallback_visual_plan(
    scenes: list[dict[str, Any]],
    topic: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Create a basic grouped plan with structured prompts if LLM planning fails."""
    style_desc = f"{profile['visual_prompt_style']}, clean educational aesthetic, high clarity, consistent style."
    visual_scenes = []

    # Group by 3 scenes if long, otherwise by 2 scenes
    group_size = 3 if len(scenes) >= 9 else 2

    scene_numbers_list = [s.get("scene_number") for s in scenes]
    current_group = []
    visual_id = 1

    for s_num in scene_numbers_list:
        current_group.append(s_num)
        if len(current_group) == group_size or s_num == scene_numbers_list[-1]:
            idx = current_group[len(current_group) // 2] - 1
            original_prompt = scenes[idx].get("visual_prompt", f"Educational illustration of {topic}")
            
            # Format in the strict structured format
            structured_prompt = (
                f"Topic: {topic}\n"
                f"Concept: Core mechanism of {topic}\n"
                f"Required visual: {original_prompt}\n"
                f"Purpose: Help viewers understand the concept visually.\n"
                f"Style: Educational documentary / realistic / cinematic, 16:9 composition, no text, no watermark"
            )

            # Fallback source classification based on prompt keywords
            source = "ai"
            query = ""
            lower_prompt = original_prompt.lower()
            lower_topic = topic.lower()
            real_keywords = ["diagram", "chart", "map", "anatomy", "history", "historical", "classic", "portrait", "structure", "geographic", "earth", "science", "biological", "cell", "organ", "skeleton", "equation"]
            if any(k in lower_prompt or k in lower_topic for k in real_keywords):
                source = "real"
                query = f"{topic} {original_prompt[:25]}".strip()

            visual_scenes.append({
                "visual_id": visual_id,
                "visual_source": source,
                "search_query": query,
                "image_prompt": structured_prompt,
                "scene_numbers": current_group
            })
            current_group = []
            visual_id += 1

    return {
        "style_description": style_desc,
        "visual_scenes": visual_scenes
    }

