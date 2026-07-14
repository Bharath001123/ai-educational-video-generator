"""Service for rendering video from scenes and merging subtitles."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import subprocess
import uuid
from pathlib import Path

from services.tts_service import (
    srt_timestamp_to_seconds,
    seconds_to_srt_timestamp,
    srt_to_vtt,
    generate_fallback_srt,
)
from services.presenter_service import generate_presenter_frames

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
GENERATED_DIR = STATIC_DIR / "generated"
VIDEOS_DIR = GENERATED_DIR / "videos"
TEMP_DIR = GENERATED_DIR / "temp"

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def url_to_path(url: str) -> Path | None:
    """Convert a local static URL to a Path object."""
    if not url:
        return None
    
    if "/static/" in url:
        relative_part = url.split("/static/")[-1]
        return STATIC_DIR / relative_part
        
    return None


def get_fontconfig_env() -> dict[str, str]:
    """Configure Fontconfig locally and return a copy of the environment.
    
    Generates a minimal fonts.conf pointing to the Windows Fonts directory and
    a temporary cache directory, returning the modified environment dictionary.
    """
    import tempfile
    env = os.environ.copy()
    
    try:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        fonts_conf_path = TEMP_DIR / "fonts.conf"
        
        cache_dir = Path(tempfile.gettempdir()) / "fontconfig_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        windir = os.environ.get("SystemRoot", "C:\\Windows")
        fonts_dir = Path(windir) / "Fonts"
        
        if not fonts_dir.exists():
            logger.warning("Windows Fonts directory not found at: %s. Subtitles might not render correctly.", fonts_dir)
            
        fonts_conf_content = f"""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
    <dir>{fonts_dir.as_posix()}</dir>
    <cachedir>{cache_dir.as_posix()}</cachedir>
</fontconfig>
"""
        fonts_conf_path.write_text(fonts_conf_content, encoding="utf-8")
        env["FONTCONFIG_FILE"] = str(fonts_conf_path)
        logger.info("Successfully configured Fontconfig environment pointing to: %s", fonts_conf_path)
    except Exception as e:
        logger.error("Failed to set up Fontconfig environment variables: %s. Subtitles may fail to render.", e, exc_info=True)
        
    return env



async def render_scene_clip(
    image_path: Path,
    audio_path: Path | None,
    duration_seconds: float,
    output_path: Path,
) -> None:
    """Create a temporary video clip for a single scene using FFmpeg.

    Uses `apad` to pad the audio with silence and freeze the frame if the actual audio
    duration is shorter than duration_seconds.
    """
    if audio_path and audio_path.exists() and audio_path.stat().st_size > 0:
        # Scene has audio voiceover
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-vf", "scale=1024:576,format=yuv420p",
            "-c:a", "aac",
            "-strict", "-2",
            "-b:a", "192k",
            "-ar", "44100",
            "-af", "apad",
            "-t", f"{duration_seconds:.3f}",
            str(output_path),
        ]
    else:
        # Scene has no voiceover: create a silent clip using lavfi anullsrc
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=mono",
            "-c:v", "libx264",
            "-vf", "scale=1024:576,format=yuv420p",
            "-c:a", "aac",
            "-strict", "-2",
            "-b:a", "192k",
            "-t", f"{duration_seconds:.3f}",
            str(output_path),
        ]

    logger.info("Rendering scene clip: %s", " ".join(cmd))
    
    def run_ffmpeg():
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
    result = await asyncio.to_thread(run_ffmpeg)

    if result.returncode != 0:
        error_msg = result.stderr.decode(errors="replace")
        logger.error("FFmpeg scene clip rendering failed: %s", error_msg)
        raise Exception(f"FFmpeg failed to render scene clip: {error_msg}")


def shift_and_reindex_srt(srt_content: str, offset: float, start_index: int) -> tuple[str, int]:
    """Shift timestamps and re-index the subtitle blocks starting from start_index.

    Returns the shifted SRT string and the next subtitle index.
    """
    blocks = re.split(r"\n\s*\n", srt_content.strip())
    processed_blocks = []
    current_idx = start_index

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        if len(lines) < 2:
            continue
        
        # Line 0: Subtitle block index
        # Line 1: Timestamp line (e.g., 00:00:01,230 --> 00:00:04,560)
        timestamp_line = lines[1]
        text_lines = lines[2:]

        match = re.match(
            r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
            timestamp_line,
        )
        if match:
            start_str, end_str = match.group(1), match.group(2)
            start_sec = srt_timestamp_to_seconds(start_str) + offset
            end_sec = srt_timestamp_to_seconds(end_str) + offset
            new_timestamp_line = (
                f"{seconds_to_srt_timestamp(start_sec)} --> "
                f"{seconds_to_srt_timestamp(end_sec)}"
            )
            
            new_block = f"{current_idx}\n{new_timestamp_line}\n" + "\n".join(text_lines)
            processed_blocks.append(new_block)
            current_idx += 1

    return "\n\n".join(processed_blocks), current_idx


def merge_scene_subtitles(scenes: list[dict]) -> tuple[str, str]:
    """Merge scene subtitles into a single master SRT and VTT string.

    Uses the render_duration (which includes padding) to align subtitle offsets.
    """
    master_srt_blocks = []
    current_offset = 0.0
    subtitle_index = 1

    for scene in scenes:
        # Use render_duration if available, otherwise fallback to actual_duration or duration_seconds
        duration = scene.get("render_duration")
        if duration is None:
            duration = scene.get("actual_duration")
        if duration is None:
            duration = float(scene.get("duration_seconds", 5.0))
            
        voiceover = scene.get("voiceover", "").strip()
        srt_filepath = scene.get("srt_filepath")

        srt_content = ""
        if srt_filepath and Path(srt_filepath).exists():
            try:
                srt_content = Path(srt_filepath).read_text(encoding="utf-8")
            except Exception as e:
                logger.error("Failed to read subtitle file %s: %s", srt_filepath, e)

        # Fallback to simple subtitle block if voiceover exists but subtitles don't
        if not srt_content.strip() and voiceover:
            srt_content = generate_fallback_srt(voiceover, duration)

        if srt_content.strip():
            shifted_content, next_idx = shift_and_reindex_srt(
                srt_content,
                current_offset,
                subtitle_index,
            )
            if shifted_content.strip():
                master_srt_blocks.append(shifted_content)
                subtitle_index = next_idx

        current_offset += duration

    master_srt = "\n\n".join(master_srt_blocks).strip()
    master_vtt = srt_to_vtt(master_srt)
    return master_srt, master_vtt


def srt_to_ass_timestamp(srt_ts: str) -> str:
    """Convert SRT timestamp '00:00:02,500' to ASS format '0:00:02.50'."""
    ts = srt_ts.replace(",", ".")
    if ts.startswith("0"):
        ts = ts[1:]
    if len(ts.split(".")[-1]) == 3:
        ts = ts[:-1]
    return ts


def convert_srt_to_ass(srt_content: str, presenter_type: str) -> str:
    """Convert master SRT subtitles to ASS format with custom margins to avoid presenter overlap."""
    margin_l = 80
    margin_r = 80
    if presenter_type and presenter_type.lower() != "none":
        margin_r = 280  # Shift text left to avoid bottom-right presenter avatar

    header = f"""[Script Info]
Title: Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1024
PlayResY: 576
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2.0,0,2,{margin_l},{margin_r},30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    blocks = srt_content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            time_line = lines[1]
            text = " ".join(lines[2:])
            
            if " --> " in time_line:
                parts = time_line.split(" --> ")
                start_ts = srt_to_ass_timestamp(parts[0].strip())
                end_ts = srt_to_ass_timestamp(parts[1].strip())
                
                # Remove HTML tags from subtitle text
                import re
                text = re.sub(r"<[^>]+>", "", text)
                
                events.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0000,0000,0000,,{text}")
                
    return header + "\n".join(events) + "\n"


async def render_video(scenes: list[dict], target_total_seconds: int, presenter_type: str = "none") -> dict:
    """Render a single merged video from scenes and combine subtitle files.

    Verifies total combined duration and adds padding if the combined audio is shorter.
    """
    fc_env = get_fontconfig_env()
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify combined audio duration and calculate padding if needed
    actual_durs = []
    for scene in scenes:
        dur = scene.get("actual_duration")
        if dur is None:
            dur = float(scene.get("duration_seconds", 5.0))
        actual_durs.append(dur)

    actual_total = sum(actual_durs)
    logger.info("Combined audio duration: %.3f seconds. Target duration: %d seconds.", actual_total, target_total_seconds)

    pad_per_scene = 0.0
    if actual_total < target_total_seconds:
        deficit = target_total_seconds - actual_total
        pad_per_scene = deficit / len(scenes)
        logger.info("Audio is shorter than target. Adding %.3f seconds padding per scene.", pad_per_scene)
    else:
        logger.info("Audio duration (%.3f seconds) is sufficient. No padding needed.", actual_total)

    # Assign render_duration to each scene
    for index, scene in enumerate(scenes):
        scene["render_duration"] = actual_durs[index] + pad_per_scene

    run_id = uuid.uuid4().hex[:10]
    temp_clip_paths: list[Path] = []
    tasks = []

    # 2. Spawn parallel FFmpeg render processes for individual scenes
    for index, scene in enumerate(scenes):
        image_url = scene.get("image_url")
        audio_url = scene.get("audio_url")
        render_duration = scene["render_duration"]

        image_path = url_to_path(image_url)
        audio_path = url_to_path(audio_url) if audio_url else None

        if not image_path or not image_path.exists():
            raise ValueError(f"Local image path does not exist for scene {scene.get('scene_number')}")

        temp_clip_path = TEMP_DIR / f"temp_{run_id}_scene_{index + 1}.mp4"
        temp_clip_paths.append(temp_clip_path)

        tasks.append(
            render_scene_clip(
                image_path=image_path,
                audio_path=audio_path,
                duration_seconds=render_duration,
                output_path=temp_clip_path,
            )
        )

    logger.info("Starting rendering of %d scene clips...", len(tasks))
    await asyncio.gather(*tasks)

    # 3. Write the concat list file
    list_file_path = TEMP_DIR / f"list_{run_id}.txt"
    with open(list_file_path, "w", encoding="utf-8") as f:
        for clip_path in temp_clip_paths:
            f.write(f"file '{clip_path.as_posix()}'\n")

    # 4. Concat individual clips into a final MP4 video
    final_video_name = f"video_{run_id}.mp4"
    final_video_path = VIDEOS_DIR / final_video_name

    concat_cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file_path),
        "-c", "copy",
        str(final_video_path),
    ]

    logger.info("Concatenating clips: %s", " ".join(concat_cmd))
    
    def run_concat():
        return subprocess.run(
            concat_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
    c_result = await asyncio.to_thread(run_concat)

    if c_result.returncode != 0:
        error_msg = c_result.stderr.decode(errors="replace")
        logger.error("FFmpeg concatenation failed: %s", error_msg)
        raise Exception(f"FFmpeg failed to concatenate clips: {error_msg}")

    # 5. Generate merged SRT and WebVTT subtitles
    master_srt, master_vtt = merge_scene_subtitles(scenes)

    final_srt_path = VIDEOS_DIR / f"video_{run_id}.srt"
    final_vtt_path = VIDEOS_DIR / f"video_{run_id}.vtt"

    final_srt_path.write_text(master_srt, encoding="utf-8")
    final_vtt_path.write_text(master_vtt, encoding="utf-8")

    # Generate ASS subtitles for FFmpeg burn-in
    final_ass_content = convert_srt_to_ass(master_srt, presenter_type)
    final_ass_path = VIDEOS_DIR / f"video_{run_id}.ass"
    final_ass_path.write_text(final_ass_content, encoding="utf-8")

    # Resolve safe relative path for FFmpeg subtitles filter on Windows to avoid colon/space issues
    abs_ass_path = final_ass_path.resolve()
    try:
        relative_ass_path = abs_ass_path.relative_to(Path(os.getcwd())).as_posix()
    except ValueError:
        relative_ass_path = abs_ass_path.as_posix().replace(":", "\\:")

    # 5b. Generate and overlay talking presenter and burn subtitles
    if presenter_type and presenter_type.lower() != "none":
        try:
            logger.info("Generating animated presenter frames for type: %s", presenter_type)
            presenter_frames_dir = TEMP_DIR / f"frames_presenter_{run_id}"
            
            await asyncio.to_thread(
                generate_presenter_frames,
                audio_path=final_video_path,
                presenter_type=presenter_type.lower(),
                frames_dir=presenter_frames_dir,
            )

            if presenter_frames_dir.exists():
                logger.info("Overlaying presenter frames and burning subtitles onto slides video...")
                overlaid_video_name = f"video_presenter_{run_id}.mp4"
                overlaid_video_path = VIDEOS_DIR / overlaid_video_name

                # Combined filter chain: overlays presenter PNG sequence AND burns ASS subtitles
                overlay_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i", str(final_video_path),
                    "-framerate", "24",
                    "-i", str(presenter_frames_dir / "frame_%05d.png"),
                    "-filter_complex",
                    f"[0:v][1:v]overlay=W-w-30:H-h-30,format=yuv420p[overlaid];"
                    f"[overlaid]subtitles={relative_ass_path}[outv]",
                    "-map", "[outv]",
                    "-map", "0:a",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "copy",
                    str(overlaid_video_path),
                ]
                
                logger.info("Running overlay command: %s", " ".join(overlay_cmd))
                
                def run_overlay():
                    return subprocess.run(
                        overlay_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=fc_env,
                    )
                
                ov_result = await asyncio.to_thread(run_overlay)
                if ov_result.returncode == 0:
                    logger.info("Successfully overlaid presenter frames and burnt subtitles.")
                    final_video_path.unlink(missing_ok=True)
                    overlaid_video_path.rename(final_video_path)
                else:
                    error_msg = ov_result.stderr.decode(errors="replace")
                    logger.error("FFmpeg overlay and subtitle burn-in failed: %s", error_msg)
                    raise Exception(f"FFmpeg overlay and subtitle burn-in failed: {error_msg}")
                
                # Cleanup frames folder
                import shutil
                shutil.rmtree(presenter_frames_dir, ignore_errors=True)
        except Exception as e:
            logger.error("Failed to generate and overlay presenter: %s", e, exc_info=True)
            raise e
    else:
        # Slides only mode: burn subtitles directly onto the slides video
        try:
            logger.info("Burning subtitles directly onto slides video...")
            overlaid_video_name = f"video_burnt_{run_id}.mp4"
            overlaid_video_path = VIDEOS_DIR / overlaid_video_name

            overlay_cmd = [
                "ffmpeg",
                "-y",
                "-i", str(final_video_path),
                "-filter_complex",
                f"[0:v]subtitles={relative_ass_path}[outv]",
                "-map", "[outv]",
                "-map", "0:a",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                str(overlaid_video_path),
            ]
            
            logger.info("Running subtitles burn-in command: %s", " ".join(overlay_cmd))
            
            def run_burn():
                return subprocess.run(
                    overlay_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=fc_env,
                )
                
            ob_result = await asyncio.to_thread(run_burn)
            if ob_result.returncode == 0:
                logger.info("Successfully burnt subtitles onto slides video.")
                final_video_path.unlink(missing_ok=True)
                overlaid_video_path.rename(final_video_path)
            else:
                error_msg = ob_result.stderr.decode(errors="replace")
                logger.error("FFmpeg subtitle burn-in failed: %s", error_msg)
                raise Exception(f"FFmpeg subtitle burn-in failed: {error_msg}")
        except Exception as e:
            logger.error("Failed to burn subtitles onto slides video: %s", e, exc_info=True)
            raise e

    # 6. Clean up temporary files
    try:
        list_file_path.unlink(missing_ok=True)
        for clip_path in temp_clip_paths:
            clip_path.unlink(missing_ok=True)
    except Exception as e:
        logger.warning("Failed to clean up some temporary rendering files: %s", e)

    video_url = f"{API_BASE_URL}/static/generated/videos/{final_video_name}"
    subtitle_url = f"{API_BASE_URL}/static/generated/videos/video_{run_id}.vtt"
    srt_url = f"{API_BASE_URL}/static/generated/videos/video_{run_id}.srt"

    return {
        "video_url": video_url,
        "video_filepath": str(final_video_path),
        "subtitle_url": subtitle_url,
        "subtitle_filepath": str(final_vtt_path),
        "srt_url": srt_url,
        "srt_filepath": str(final_srt_path),
    }
