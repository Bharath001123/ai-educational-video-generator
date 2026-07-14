# Project Context – Subtitle Burning Fix

## Root Cause
The Windows environment lacked a proper Fontconfig configuration, causing **libass** (used by FFmpeg for ASS subtitle rendering) to be unable to locate system fonts. As a result, the subtitle‑burning step silently failed, producing an MP4 without visible captions while the web player still received the generated `.vtt` file.

## Solution
Implemented `ensure_fontconfig()` in **render_service.py** to:
- Set up a minimal Fontconfig XML configuration on Windows.
- Export `FONTCONFIG_FILE` via the subprocess environment when invoking FFmpeg.
- Log a warning if the configuration cannot be applied, allowing graceful fallback.

## Subtitle Flow
1. **Web Player** – Generates a `.vtt` file for in‑browser subtitles (unchanged).
2. **Burned Subtitles** – The `.ass` file is passed to FFmpeg with the `subtitles=` filter, using the Fontconfig setup to render subtitles directly onto the video frames.
3. **Download API** – Returns the MP4 that includes the burned‑in subtitles (the final output delivered to users).

## Verification Completed
- **Presenter Modes**:
  - Female Teacher
  - Male Teacher
  - Robot Teacher
  - Slides Only
- **Playback Tests**:
  - VLC confirms subtitles are visible.
  - Windows Media Player confirms subtitles are visible.

## Current Status
The subtitle‑burning issue is fully resolved. The downloaded MP4 now contains visible subtitles, while the `.vtt` file continues to serve the web player.
