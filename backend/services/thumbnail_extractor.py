import subprocess
from pathlib import Path

def extract_thumbnail(video_path: Path, thumb_path: Path, timestamp: float = 2.0) -> None:
    """Extract a thumbnail from *video_path*.
    Attempts to capture a frame at *timestamp* seconds; if FFmpeg fails, falls back to the first frame.
    The thumbnail is scaled to a width of 320 px (preserving aspect ratio).
    """
    # Ensure destination directory exists
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    # Primary attempt at the specified timestamp
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(timestamp),
        "-i",
        str(video_path),
        "-vf",
        "scale=320:-1",
        "-vframes",
        "1",
        str(thumb_path),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Fallback: first frame (no -ss)
        fallback_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            "scale=320:-1",
            "-vframes",
            "1",
            str(thumb_path),
        ]
        subprocess.run(fallback_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
