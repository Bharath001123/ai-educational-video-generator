"""AI image generation service for video scenes.

Generates images from visual prompts using an external API.
Replace `_call_image_api` when switching providers.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GENERATED_IMAGES_DIR = Path(__file__).resolve().parent.parent / "static" / "generated"
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
OPENAI_IMAGE_SIZE = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def generate_scene_image(prompt: str, scene_number: int = 1) -> str:
    """Generate an image for a scene visual prompt and save it locally."""
    try:
        remote_url = _call_image_api(prompt)
        logger.info("Generated remote image URL: %s", remote_url)
        local_url = _download_and_save_image(remote_url, scene_number)
        return local_url

    except Exception as error:
        logger.error(
            "Image generation/download failed for scene %s: %s",
            scene_number,
            error,
            exc_info=True,
        )
        try:
            placeholder_url = get_placeholder_image_url(scene_number)
            local_placeholder_url = _download_and_save_image(placeholder_url, scene_number)
            return local_placeholder_url
        except Exception as placeholder_error:
            logger.error("Failed to download placeholder: %s", placeholder_error)
            return get_placeholder_image_url(scene_number)


def get_placeholder_image_url(scene_number: int) -> str:
    """Return a placeholder image URL when generation fails."""
    label = quote(f"Scene {scene_number}")
    return f"https://placehold.co/1024x576/1e293b/94a3b8.jpg?text={label}"


def _call_image_api(prompt: str) -> str:
    """Generate image using Pollinations AI (free)."""
    encoded_prompt = quote(prompt)
    image_url = (
        "https://image.pollinations.ai/prompt/"
        f"{encoded_prompt}?width=1024&height=576"
    )
    return image_url


def _download_and_save_image(image_url: str, scene_number: int) -> str:
    """Download a remote image and store it locally for serving."""
    GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"scene_{scene_number}_{uuid.uuid4().hex[:10]}.jpg"
    file_path = GENERATED_IMAGES_DIR / filename

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    with httpx.Client(headers=headers, timeout=60.0) as client:
        response = client.get(image_url, follow_redirects=True)
        response.raise_for_status()
        file_path.write_bytes(response.content)

    return f"{API_BASE_URL}/static/generated/{filename}"


def search_wikimedia_commons(query: str, max_results: int = 5) -> list[str]:
    """Search Wikimedia Commons for images matching the query.
    
    Filters and returns only direct URLs to .jpg, .jpeg, or .png images.
    """
    url = "https://commons.wikimedia.org/w/api.php"
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": "6",  # Namespace 6 is Files
        "format": "json",
        "utf8": "1"
    }
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        with httpx.Client(headers=headers, timeout=10.0) as client:
            response = client.get(url, params=search_params)
            response.raise_for_status()
            data = response.json()
            
            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                logger.info("No Wikimedia Commons search results found for query: %s", query)
                return []
                
            titles = [item.get("title") for item in search_results[:max_results] if item.get("title")]
            if not titles:
                return []
                
            # Query the image URLs for all titles in a single API call to prevent rate limiting (429)
            info_params = {
                "action": "query",
                "titles": "|".join(titles),
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json"
            }
            info_response = client.get(url, params=info_params)
            info_response.raise_for_status()
            info_data = info_response.json()
            
            pages = info_data.get("query", {}).get("pages", {})
            image_urls = []
            for page_id, page_data in pages.items():
                imageinfo = page_data.get("imageinfo", [])
                if imageinfo:
                    img_url = imageinfo[0].get("url")
                    if img_url:
                        # Avoid SVGs/TIFFs due to FFmpeg rendering compatibility
                        img_url_lower = img_url.lower()
                        if img_url_lower.endswith((".jpg", ".jpeg", ".png")):
                            image_urls.append(img_url)
            return image_urls
            
    except Exception as e:
        logger.error("Error searching Wikimedia Commons: %s", e)
        return []


def retrieve_real_image(query: str, scene_number: int) -> str | None:
    """Search for a real image on Wikimedia Commons and download it.
    
    Returns the local URL of the downloaded image, or None if retrieval fails.
    """
    try:
        urls = search_wikimedia_commons(query, max_results=5)
        if not urls:
            logger.warning("No Wikimedia Commons search results found for query: %s", query)
            return None
            
        for url in urls:
            try:
                logger.info("Attempting to download real image from Wikimedia: %s", url)
                local_url = _download_and_save_image(url, scene_number)
                return local_url
            except Exception as download_error:
                logger.warning(
                    "Failed to download image from %s: %s. Trying next candidate...",
                    url,
                    download_error
                )
        logger.warning("All Wikimedia Commons image downloads failed for query: %s", query)
        return None
    except Exception as error:
        logger.error("Real image retrieval failed for query %s: %s", query, error, exc_info=True)
        return None

