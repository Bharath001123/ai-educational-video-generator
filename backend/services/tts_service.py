"""Text-to-Speech voice generation service for scene voiceovers.

Uses edge-tts (neural) as the primary provider and falls back to gTTS.
Avoids redundant synthesis using a stable hash cache.
Generates WebVTT and SRT subtitle files along with voiceover.
"""

from __future__ import annotations

import hashlib
import logging
import os
import asyncio
import re
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import edge_tts
from gtts import gTTS

load_dotenv()

logger = logging.getLogger(__name__)

GENERATED_AUDIO_DIR = Path(__file__).resolve().parent.parent / "static" / "generated" / "audio"
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# Voice mappings for edge-tts (Neural)
EDGE_VOICES = {
    "english": "en-US-GuyNeural",
    "hindi": "hi-IN-MadhurNeural",
    "telugu": "te-IN-MohanNeural",
}

# Language codes for gTTS fallback
GTTS_LANGS = {
    "english": "en",
    "hindi": "hi",
    "telugu": "te",
}


def srt_timestamp_to_seconds(ts: str) -> float:
    """Convert SRT timestamp (HH:MM:SS,mmm) to seconds (float)."""
    parts = ts.split(",")
    ms = float(parts[1]) / 1000.0 if len(parts) > 1 else 0.0
    hms = parts[0].split(":")
    hours = float(hms[0])
    minutes = float(hms[1])
    seconds = float(hms[2])
    return hours * 3600 + minutes * 60 + seconds + ms


def seconds_to_srt_timestamp(seconds: float) -> str:
    """Convert seconds (float) to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    secs_int = int(secs)
    ms = int(round((secs - secs_int) * 1000))
    if ms >= 1000:
        secs_int += 1
        ms -= 1000
    return f"{hours:02d}:{minutes:02d}:{secs_int:02d},{ms:03d}"


def srt_to_vtt(srt_content: str) -> str:
    """Convert SRT subtitle content to WebVTT format."""
    vtt_content = re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", srt_content)
    return "WEBVTT\n\n" + vtt_content


def get_audio_duration(file_path: Path) -> float:
    """Get the duration of an audio file in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.error("Failed to get audio duration for %s: %s", file_path, e)
        return 5.0  # Fallback


def generate_fallback_srt(text: str, duration: float) -> str:
    """Generate basic subtitles by splitting text into sentences and distributing them."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        sentences = [text]

    num_sentences = len(sentences)
    sentence_duration = duration / num_sentences

    srt_lines = []
    for i, sentence in enumerate(sentences):
        start_sec = i * sentence_duration
        end_sec = (i + 1) * sentence_duration - 0.1
        if end_sec < start_sec:
            end_sec = start_sec

        start_ts = seconds_to_srt_timestamp(start_sec)
        end_ts = seconds_to_srt_timestamp(end_sec)

        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{start_ts} --> {end_ts}")
        srt_lines.append(sentence)
        srt_lines.append("")

    return "\n".join(srt_lines)


async def generate_voiceovers_for_scenes(scenes: list[dict], language: str) -> list[dict]:
    """Generate audio and subtitle files for each scene and attach URLs/filepaths."""
    GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    enriched_scenes: list[dict] = []

    for scene in scenes:
        voiceover_text = scene.get("voiceover", "").strip()
        if not voiceover_text:
            enriched_scenes.append(scene)
            continue

        # Generate a stable hash using md5 of text + language
        normalized_lang = language.lower().strip()
        text_bytes = f"{voiceover_text}:{normalized_lang}".encode("utf-8")
        text_hash = hashlib.md5(text_bytes).hexdigest()
        
        audio_filename = f"tts_{text_hash}.mp3"
        srt_filename = f"tts_{text_hash}.srt"
        vtt_filename = f"tts_{text_hash}.vtt"
        
        audio_path = GENERATED_AUDIO_DIR / audio_filename
        srt_path = GENERATED_AUDIO_DIR / srt_filename
        vtt_path = GENERATED_AUDIO_DIR / vtt_filename

        audio_url = f"{API_BASE_URL}/static/generated/audio/{audio_filename}"
        subtitle_url = f"{API_BASE_URL}/static/generated/audio/{vtt_filename}"

        # Generate only if files do not exist or are empty
        audio_exists = audio_path.exists() and audio_path.stat().st_size > 0
        subtitles_exist = srt_path.exists() and srt_path.stat().st_size > 0 and vtt_path.exists()

        if audio_exists and subtitles_exist:
            logger.info("Found cached audio and subtitles for scene %s", scene.get("scene_number", "?"))
            success = True
        else:
            logger.info("Synthesizing audio and subtitles for scene %s", scene.get("scene_number", "?"))
            success = await generate_audio_and_subs(voiceover_text, normalized_lang, audio_path, srt_path, vtt_path)

        scene_copy = {**scene}
        if success:
            scene_copy["audio_url"] = audio_url
            scene_copy["audio_filepath"] = str(audio_path)
            scene_copy["subtitle_url"] = subtitle_url
            scene_copy["subtitle_filepath"] = str(vtt_path)
            scene_copy["srt_filepath"] = str(srt_path)
            # Find the actual duration of the generated audio to keep timing completely accurate
            actual_duration = get_audio_duration(audio_path)
            scene_copy["actual_duration"] = actual_duration
        else:
            scene_copy["audio_url"] = None
            scene_copy["audio_filepath"] = None
            scene_copy["subtitle_url"] = None
            scene_copy["subtitle_filepath"] = None
            scene_copy["srt_filepath"] = None
            scene_copy["actual_duration"] = scene.get("duration_seconds", 5)

        enriched_scenes.append(scene_copy)

    return enriched_scenes


async def generate_audio_and_subs(
    text: str,
    language: str,
    audio_path: Path,
    srt_path: Path,
    vtt_path: Path,
) -> bool:
    """Synthesize voiceover and subtitles using edge-tts, falling back to gTTS."""
    try:
        await _generate_with_edge_tts(text, language, audio_path, srt_path, vtt_path)
        return True
    except Exception as edge_error:
        logger.warning(
            "Edge-TTS synthesis failed. Falling back to gTTS. Error: %s",
            edge_error,
            exc_info=True,
        )
        try:
            # Generate audio synchronously using gTTS fallback
            await asyncio.to_thread(_generate_with_gtts, text, language, audio_path)
            
            # Generate fallback subtitles using gTTS audio duration
            duration = get_audio_duration(audio_path)
            srt_content = generate_fallback_srt(text, duration)
            srt_path.write_text(srt_content, encoding="utf-8")
            
            vtt_content = srt_to_vtt(srt_content)
            vtt_path.write_text(vtt_content, encoding="utf-8")
            return True
        except Exception as gtts_error:
            logger.error(
                "Both Edge-TTS and gTTS fallback failed. Error: %s",
                gtts_error,
                exc_info=True,
            )
            return False


async def _generate_with_edge_tts(
    text: str,
    language: str,
    audio_path: Path,
    srt_path: Path,
    vtt_path: Path,
) -> None:
    """Call Edge-TTS API and feed boundary metadata to SubMaker to write srt and vtt."""
    voice = EDGE_VOICES.get(language, EDGE_VOICES["english"])
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            else:
                submaker.feed(chunk)

    # Save subtitles
    srt_content = submaker.get_srt()
    srt_path.write_text(srt_content, encoding="utf-8")

    vtt_content = srt_to_vtt(srt_content)
    vtt_path.write_text(vtt_content, encoding="utf-8")


def _generate_with_gtts(text: str, language: str, file_path: Path) -> None:
    """Call Google TTS API synchronously to generate fallback audio."""
    lang_code = GTTS_LANGS.get(language, GTTS_LANGS["english"])
    tts = gTTS(text=text, lang=lang_code)
    tts.save(file_path)
