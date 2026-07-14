"""Presenter service for generating talking AI teacher animations.

Procedurally draws a flat-design character (Female, Male, Robot) using Pillow
and syncs mouth open height with audio amplitude dynamically.
"""

from __future__ import annotations

import logging
import math
import os
import shutil
import struct
import subprocess
import uuid
import wave
from pathlib import Path
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

TEMP_DIR = Path(__file__).resolve().parent.parent / "static" / "generated" / "temp"


def draw_female_teacher(draw: ImageDraw.ImageDraw, frame_idx: int, mouth_open_ratio: float) -> None:
    """Draw a female teacher cartoon character on the canvas (240x240)."""
    # Simple sway for breathing/animation
    sway = int(math.sin(frame_idx * 0.15) * 3)

    # Hair back
    draw.ellipse([56, 56 + sway, 184, 208 + sway], fill=(60, 40, 30, 255))

    # Torso (Shoulders/Blazer)
    draw.polygon([(48, 224), (192, 224), (160, 184), (80, 184)], fill=(220, 50, 80, 255))
    # Inner shirt
    draw.polygon([(104, 184), (136, 184), (120, 204)], fill=(255, 255, 255, 255))

    # Neck
    draw.rectangle([108, 156 + sway, 132, 188 + sway], fill=(253, 219, 197, 255))

    # Head / Face
    draw.ellipse([76, 76 + sway, 164, 164 + sway], fill=(253, 219, 197, 255))

    # Hair front (Bangs/sides)
    draw.chord([72, 64 + sway, 168, 128 + sway], start=180, end=360, fill=(60, 40, 30, 255))
    draw.rectangle([72, 96 + sway, 88, 160 + sway], fill=(60, 40, 30, 255))
    draw.rectangle([152, 96 + sway, 168, 160 + sway], fill=(60, 40, 30, 255))

    # Eyes & Blinking
    is_blinking = (frame_idx % 90) < 3
    if is_blinking:
        draw.line([92, 112 + sway, 108, 112 + sway], fill=(0, 0, 0, 255), width=2)
        draw.line([132, 112 + sway, 148, 112 + sway], fill=(0, 0, 0, 255), width=2)
    else:
        # Glasses frames & bridge
        draw.ellipse([88, 100 + sway, 112, 124 + sway], outline=(0, 0, 0, 255), width=2)
        draw.ellipse([128, 100 + sway, 152, 124 + sway], outline=(0, 0, 0, 255), width=2)
        draw.line([112, 112 + sway, 128, 112 + sway], fill=(0, 0, 0, 255), width=2)
        # Pupils
        draw.ellipse([97, 109 + sway, 103, 115 + sway], fill=(0, 0, 0, 255))
        draw.ellipse([137, 109 + sway, 143, 115 + sway], fill=(0, 0, 0, 255))

    # Mouth
    if mouth_open_ratio < 0.1:
        # Smile arc
        draw.arc([108, 130 + sway, 132, 142 + sway], start=0, end=180, fill=(150, 40, 40, 255), width=2)
    else:
        # Open oval
        h = int(10 * mouth_open_ratio)
        draw.ellipse([110, 138 - h + sway, 130, 138 + h + sway], fill=(120, 20, 20, 255))
        if mouth_open_ratio > 0.5:
            # Teeth
            draw.rectangle([114, 138 - h + 2 + sway, 126, 138 - h + 4 + sway], fill=(255, 255, 255, 255))


def draw_male_teacher(draw: ImageDraw.ImageDraw, frame_idx: int, mouth_open_ratio: float) -> None:
    """Draw a male teacher cartoon character on the canvas (240x240)."""
    sway = int(math.sin(frame_idx * 0.15) * 3)

    # Torso (Shirt)
    draw.polygon([(48, 224), (192, 224), (160, 184), (80, 184)], fill=(30, 120, 180, 255))
    # Collar
    draw.polygon([(92, 184), (108, 200), (120, 184)], fill=(20, 100, 160, 255))
    draw.polygon([(148, 184), (132, 200), (120, 184)], fill=(20, 100, 160, 255))

    # Neck
    draw.rectangle([108, 156 + sway, 132, 188 + sway], fill=(240, 200, 180, 255))

    # Head / Face
    draw.ellipse([76, 76 + sway, 164, 164 + sway], fill=(240, 200, 180, 255))

    # Hair
    draw.ellipse([72, 64 + sway, 168, 100 + sway], fill=(40, 40, 40, 255))

    # Eyes & Blinking
    is_blinking = (frame_idx % 90) < 3
    if is_blinking:
        draw.line([92, 112 + sway, 108, 112 + sway], fill=(0, 0, 0, 255), width=2)
        draw.line([132, 112 + sway, 148, 112 + sway], fill=(0, 0, 0, 255), width=2)
    else:
        # Glasses frames & bridge
        draw.rectangle([88, 100 + sway, 112, 124 + sway], outline=(30, 30, 30, 255), width=2)
        draw.rectangle([128, 100 + sway, 152, 124 + sway], outline=(30, 30, 30, 255), width=2)
        draw.line([112, 112 + sway, 128, 112 + sway], fill=(30, 30, 30, 255), width=2)
        # Pupils
        draw.ellipse([97, 109 + sway, 103, 115 + sway], fill=(0, 0, 0, 255))
        draw.ellipse([137, 109 + sway, 143, 115 + sway], fill=(0, 0, 0, 255))

    # Mouth
    if mouth_open_ratio < 0.1:
        draw.arc([108, 130 + sway, 132, 142 + sway], start=0, end=180, fill=(150, 40, 40, 255), width=2)
    else:
        h = int(10 * mouth_open_ratio)
        draw.ellipse([110, 138 - h + sway, 130, 138 + h + sway], fill=(120, 20, 20, 255))
        if mouth_open_ratio > 0.5:
            draw.rectangle([114, 138 - h + 2 + sway, 126, 138 - h + 4 + sway], fill=(255, 255, 255, 255))


def draw_robot_teacher(draw: ImageDraw.ImageDraw, frame_idx: int, mouth_open_ratio: float) -> None:
    """Draw a robot teacher cartoon character on the canvas (240x240)."""
    sway = int(math.sin(frame_idx * 0.15) * 3)

    # Torso (Metallic shoulders)
    draw.polygon([(56, 224), (184, 224), (152, 184), (88, 184)], fill=(90, 110, 130, 255))
    # Glowing chest center
    draw.ellipse([108, 196, 132, 220], fill=(0, 220, 255, 255))

    # Neck
    draw.rectangle([110, 156 + sway, 130, 188 + sway], fill=(120, 140, 160, 255))

    # Head / Screen body
    draw.rectangle([76, 76 + sway, 164, 156 + sway], fill=(100, 120, 140, 255))
    # Dark grey screen insert
    draw.rectangle([84, 84 + sway, 156, 148 + sway], fill=(30, 40, 50, 255))

    # Ears/Antennas
    draw.rectangle([68, 108 + sway, 76, 124 + sway], fill=(80, 100, 120, 255))
    draw.rectangle([164, 108 + sway, 172, 124 + sway], fill=(80, 100, 120, 255))
    # Antenna on top
    draw.line([120, 76 + sway, 120, 60 + sway], fill=(120, 140, 160, 255), width=3)
    draw.ellipse([115, 55 + sway, 125, 65 + sway], fill=(255, 50, 50, 255))

    # Eyes (LED style)
    is_blinking = (frame_idx % 90) < 3
    if is_blinking:
        draw.line([92, 104 + sway, 108, 104 + sway], fill=(0, 255, 200, 255), width=2)
        draw.line([132, 104 + sway, 148, 104 + sway], fill=(0, 255, 200, 255), width=2)
    else:
        # Glowing green circular grids
        draw.ellipse([92, 96 + sway, 108, 112 + sway], fill=(0, 255, 200, 255))
        draw.ellipse([132, 96 + sway, 148, 112 + sway], fill=(0, 255, 200, 255))
        # Pupils
        draw.ellipse([97, 101 + sway, 103, 107 + sway], fill=(0, 50, 50, 255))
        draw.ellipse([137, 101 + sway, 143, 107 + sway], fill=(0, 50, 50, 255))

    # Mouth (LED display waveform)
    if mouth_open_ratio < 0.1:
        # Flat LED line
        draw.line([104, 132 + sway, 136, 132 + sway], fill=(0, 255, 200, 255), width=3)
    else:
        # Waveform bars
        h = int(12 * mouth_open_ratio)
        draw.line([104, 132 + sway, 136, 132 + sway], fill=(0, 255, 200, 255), width=2)
        # Center bar
        draw.line([120, 132 - h + sway, 120, 132 + h + sway], fill=(0, 255, 200, 255), width=3)
        # Side bars
        h_side = int(h * 0.6)
        draw.line([112, 132 - h_side + sway, 112, 132 + h_side + sway], fill=(0, 255, 200, 255), width=3)
        draw.line([128, 132 - h_side + sway, 128, 132 + h_side + sway], fill=(0, 255, 200, 255), width=3)


def get_audio_volume_profile(wav_path: Path, num_frames: int, video_fps: int = 24) -> list[float]:
    """Analyze wav file raw samples to calculate average volume ratios per video frame."""
    try:
        with wave.open(str(wav_path), "rb") as wav:
            params = wav.getparams()
            n_channels = params.nchannels
            sampwidth = params.sampwidth
            framerate = params.framerate
            n_frames = wav.getnframes()

            raw_data = wav.readframes(n_frames)

        # Ensure 16-bit PCM format
        if sampwidth != 2:
            logger.warning("Unexpected audio sample width %s in WAV. Defaulting to flat volume profile.", sampwidth)
            return [0.0] * num_frames

        count = len(raw_data) // 2
        # Unpack little-endian shorts
        samples = struct.unpack(f"<{count}h", raw_data)

        # If stereo, average channels
        if n_channels == 2:
            samples = [(samples[i] + samples[i + 1]) // 2 for i in range(0, len(samples), 2)]

        samples_per_video_frame = framerate / video_fps
        ratios = []

        for frame_idx in range(num_frames):
            start_sample = int(frame_idx * samples_per_video_frame)
            end_sample = int((frame_idx + 1) * samples_per_video_frame)
            
            segment = samples[start_sample:end_sample]
            if not segment:
                ratios.append(0.0)
                continue

            abs_avg = sum(abs(s) for s in segment) / len(segment)
            # Normalize against typical high speaking voice amplitude
            ratio = min(abs_avg / 8000.0, 1.0)
            ratios.append(ratio)

        return ratios

    except Exception as e:
        logger.error("Failed to analyze audio volume profile: %s", e, exc_info=True)
        return [0.0] * num_frames


def generate_presenter_frames(
    audio_path: Path,
    presenter_type: str,
    frames_dir: Path,
    video_fps: int = 24,
) -> int:
    """Generate transparent talking presenter frames synced to input audio."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    run_id = uuid.uuid4().hex[:10]
    temp_wav_path = TEMP_DIR / f"temp_{run_id}.wav"

    # 1. Convert audio to mono 16kHz WAV using FFmpeg for wave reading
    conv_cmd = [
        "ffmpeg",
        "-y",
        "-i", str(audio_path),
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(temp_wav_path)
    ]
    logger.info("Converting audio for analysis: %s", " ".join(conv_cmd))
    subprocess.run(conv_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    try:
        # Determine total duration of audio in seconds
        with wave.open(str(temp_wav_path), "rb") as wav:
            audio_frames = wav.getnframes()
            audio_rate = wav.getframerate()
            duration_seconds = audio_frames / audio_rate

        total_frames = max(1, int(duration_seconds * video_fps))
        logger.info("Generating %d transparent presenter frames (%.2f seconds)...", total_frames, duration_seconds)

        # 2. Get mouth opening ratios frame by frame
        volume_ratios = get_audio_volume_profile(temp_wav_path, total_frames, video_fps)

        # Choose drawing function
        drawer = None
        if presenter_type == "female":
            drawer = draw_female_teacher
        elif presenter_type == "male":
            drawer = draw_male_teacher
        elif presenter_type == "robot":
            drawer = draw_robot_teacher

        if not drawer:
            raise ValueError(f"Unknown presenter type: {presenter_type}")

        # 3. Draw frames with transparent background
        for frame_idx in range(total_frames):
            img = Image.new("RGBA", (240, 240), (0, 0, 0, 0)) # Transparent background
            draw = ImageDraw.Draw(img)
            
            mouth_open_ratio = volume_ratios[frame_idx]
            drawer(draw, frame_idx, mouth_open_ratio)

            frame_file = frames_dir / f"frame_{frame_idx:05d}.png"
            img.save(frame_file)

        logger.info("Successfully generated %d transparent frames in %s", total_frames, frames_dir)
        return total_frames

    finally:
        # Cleanup temporary WAV file
        temp_wav_path.unlink(missing_ok=True)
