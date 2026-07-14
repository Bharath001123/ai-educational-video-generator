"""Video generation orchestration service.

Combines script generation with per-scene image generation,
voiceovers, subtitles, and final video rendering.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import logging

from services.image_service import generate_scene_image
from services.script_service import generate_script
from services.tts_service import generate_voiceovers_for_scenes
from services.render_service import render_video
from services.scene_converter import DURATION_SECONDS
from services.visual_planner import plan_and_attach_visuals

logger = logging.getLogger(__name__)


async def generate_video_content(
    topic: str,
    audience: str,
    duration: str,
    language: str,
    presenter_type: str = "none",
) -> dict:
    """Generate a full video script with images, audio, subtitles, and render it to MP4."""
    logger.info("STAGE 1: Request Validation. Params: topic=%s, audience=%s, duration=%s, language=%s, presenter=%s",
                topic, audience, duration, language, presenter_type)

    logger.info("STAGE 2: Script Generation starting...")
    script = await asyncio.to_thread(
        generate_script,
        topic=topic,
        audience=audience,
        duration=duration,
        language=language,
    )
    if not script or "scenes" not in script or not script["scenes"]:
        raise ValueError("Script generation failed: script structure is empty or invalid.")
    logger.info("STAGE 2: Script Generation complete. Title: %s, Scenes: %d", script.get("title"), len(script["scenes"]))

    logger.info("STAGE 3: Visual Planning and Image Retrieval starting...")
    script["scenes"] = await asyncio.to_thread(
        plan_and_attach_visuals,
        scenes=script.get("scenes", []),
        topic=topic,
        audience=audience,
        duration=duration,
    )
    if not script["scenes"]:
        raise ValueError("Visual Planning failed: scene array is empty.")
    logger.info("STAGE 3: Visual Planning complete. Planned %d scenes.", len(script["scenes"]))

    logger.info("STAGE 4: TTS Voiceover & Subtitles Generation starting...")
    script["scenes"] = await generate_voiceovers_for_scenes(
        script["scenes"], 
        language=language
    )
    logger.info("STAGE 4: TTS complete.")

    script["metadata"]["images_generated"] = sum(
        1 for scene in script["scenes"] if scene.get("image_url")
    )
    script["metadata"]["audio_generated"] = sum(
        1 for scene in script["scenes"] if scene.get("audio_url")
    )

    logger.info("STAGE 5: Final Video Rendering (FFmpeg compilation & Presenter Overlay) starting...")
    target_total_seconds = DURATION_SECONDS.get(duration, 180)
    
    # We do NOT swallow exceptions. If rendering fails, let the error propagate immediately.
    render_results = await render_video(script["scenes"], target_total_seconds, presenter_type=presenter_type)
    
    video_filepath_str = render_results.get("video_filepath")
    if not video_filepath_str:
        raise FileNotFoundError("Video rendering failed: no video filepath returned.")
        
    video_path = Path(video_filepath_str)
    if not video_path.exists():
        raise FileNotFoundError(f"Video rendering failed: output file does not exist at {video_path}")
    if video_path.stat().st_size == 0:
        raise ValueError(f"Video rendering failed: output file at {video_path} is empty (0 bytes).")

    logger.info("STAGE 5: Video rendering complete. File exists at %s (%d bytes)", video_path, video_path.stat().st_size)

    script["video_url"] = render_results.get("video_url")
    script["subtitle_url"] = render_results.get("subtitle_url")
    script["srt_url"] = render_results.get("srt_url")
    script["metadata"]["video_rendered"] = True
    script["metadata"]["presenter_type"] = presenter_type

    # ------------------------------------------------------------
    # Post‑processing: thumbnail extraction + metadata persistence
    # ------------------------------------------------------------
    try:
        from services.thumbnail_extractor import extract_thumbnail
        from services.metadata_store import add_record, init_db
        from datetime import datetime
        import subprocess
        # Ensure DB exists
        init_db()
        # -----------------------------------------------------------------
        # Thumbnail extraction (around 2 seconds, fallback to first frame)
        # -----------------------------------------------------------------
        thumb_rel_path = f"generated/thumbnails/{video_path.stem}.png"
        thumb_abs_path = Path(__file__).resolve().parent.parent / "static" / thumb_rel_path
        # Use ffmpeg to grab a frame at 2 s; if it fails, fallback to the first frame
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    "2",
                    "-i",
                    str(video_path),
                    "-vf",
                    "scale=320:-1",
                    "-vframes",
                    "1",
                    str(thumb_abs_path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # Fallback: first frame
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(video_path),
                    "-vf",
                    "scale=320:-1",
                    "-vframes",
                    "1",
                    str(thumb_abs_path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        # -----------------------------------------------------------------
        # Gather extended metadata
        # -----------------------------------------------------------------
        video_stat = video_path.stat()
        metadata_record = {
            "title": script.get("title", "Untitled"),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "duration": target_total_seconds,
            "presenter_type": presenter_type,
            "voice": script["metadata"].get("voice"),
            "language": language,
            "file_size": video_stat.st_size,
            "resolution": None,  # could be derived via ffprobe later
            "thumbnail_path": f"/static/{thumb_rel_path}",
            "video_path": script.get("video_url"),
            "subtitle_path": script.get("subtitle_url"),
            "status": "completed",
        }
        add_record(metadata_record)
    except Exception as e:
        logger.error("Post‑processing (thumbnail/metadata) failed: %s", e)
        # Continue without raising; the API response already contains the video URLs.


    return script


def attach_images_to_scenes(scenes: list[dict]) -> list[dict]:
    """Generate an image for every scene and attach the URL."""
    enriched_scenes: list[dict] = []

    for scene in scenes:
        scene_number = scene.get("scene_number", len(enriched_scenes) + 1)
        visual_prompt = scene.get("visual_prompt", "")

        logger.info("Generating image for scene %s", scene_number)
        image_url = generate_scene_image(visual_prompt, scene_number=scene_number)

        enriched_scenes.append(
            {
                **scene,
                "image_url": image_url,
            }
        )

    return enriched_scenes
