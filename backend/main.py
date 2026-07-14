import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import datetime

from services.openai_service import MissingAPIKeyError, OpenAIAPIError
from services.video_service import generate_video_content
from services.metadata_store import list_records, add_record, delete_record
from services.thumbnail_extractor import extract_thumbnail

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="AI Educational Video Generator",
    description="Backend API for the AI-Based Automated Educational Video Generation System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
GENERATED_DIR = STATIC_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class VideoRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    audience: str
    duration: str
    language: str
    presenter_type: str = "none"


@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Educational Video Generator API",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/generate")
async def generate_video(request: VideoRequest):
    topic = request.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    try:
        script = await generate_video_content(
            topic=topic,
            audience=request.audience,
            duration=request.duration,
            language=request.language,
            presenter_type=request.presenter_type,
        )

    except MissingAPIKeyError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except OpenAIAPIError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI returned invalid script JSON: {error}",
        ) from error

    return {
        "message": "Video generation request received successfully",
        "topic": topic,
        "audience": request.audience,
        "duration": request.duration,
        "language": request.language,
        "script": script,
        "video_url": script.get("video_url"),
        "subtitle_url": script.get("subtitle_url"),
    }

# ------------------------------------------------------------
# Library endpoint
# ------------------------------------------------------------

@app.get("/api/library")
async def get_library():
    """Return list of stored video metadata records.
    Generates missing thumbnails for videos that lack a thumbnail_path.
    """
    records = list_records()
    # Ensure thumbnails exist for each record
    for record in records:
        if not record.get("thumbnail_path"):
            video_url = record.get("video_path")
            if video_url:
                static_dir = Path(__file__).resolve().parent / "static"
                url_path = video_url.replace("/static/", "")
                video_path_obj = static_dir / url_path
                if video_path_obj.exists():
                    thumb_name = video_path_obj.stem + "_thumb.jpg"
                    thumb_path_obj = video_path_obj.parent / thumb_name
                    if not thumb_path_obj.exists():
                        extract_thumbnail(video_path_obj, thumb_path_obj)
                    # Update DB with new thumbnail path
                    rel_dir = video_path_obj.parent.relative_to(static_dir)
                    thumbnail_url = f"/static/{rel_dir}/{thumb_name}"
                    # Update record in DB
                    from services.metadata_store import update_thumbnail
                    update_thumbnail(record["id"], thumbnail_url)
    return {"videos": list_records()}

@app.post("/api/library/save")
async def save_to_library(payload: dict):
    """Save generated video metadata to the library."""
    try:
        video_url = payload.get("video_url")
        if not video_url:
            raise HTTPException(status_code=400, detail="Missing video_url in payload")
            
        existing = list_records()
        for record in existing:
            if record.get("video_path") == video_url:
                raise HTTPException(status_code=400, detail="This video is already in your library.")
                
        static_dir = Path(__file__).resolve().parent / "static"
        url_path = video_url.replace("/static/", "")
        video_path_obj = static_dir / url_path
        
        file_size = 0
        if video_path_obj.exists():
            file_size = video_path_obj.stat().st_size
            
        metadata = payload.get("metadata", {})
        
        duration_val = payload.get("duration") or metadata.get("duration", 0)
        try:
            duration_int = int(float(duration_val))
        except (ValueError, TypeError):
            duration_int = 0
            
        thumb_name = video_path_obj.stem + "_thumb.jpg"
        thumb_path_obj = video_path_obj.parent / thumb_name
        # Generate thumbnail if it does not exist
        if not thumb_path_obj.exists():
            extract_thumbnail(video_path_obj, thumb_path_obj)
        # Determine thumbnail URL relative to STATIC_DIR
        rel_dir = video_path_obj.parent.relative_to(STATIC_DIR)
        thumbnail_path = f"/static/{rel_dir}/{thumb_name}" if thumb_path_obj.exists() else None

        record = {
            "title": payload.get("title", metadata.get("topic", "Untitled")),
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "duration": duration_int,
            "presenter_type": metadata.get("presenter_type", "none"),
            "voice": metadata.get("voice", "alloy"),
            "language": metadata.get("language", "english"),
            "file_size": file_size,
            "resolution": "1080x1920",
            "thumbnail_path": thumbnail_path,
            "video_path": video_url,
            "subtitle_path": payload.get("subtitle_url"),
            "status": "completed"
        }
        
        add_record(record)
        return {"message": "Video saved successfully", "record": record}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/library/{record_id}")
async def delete_from_library(record_id: int):
    """Delete a video record from the library."""
    success = delete_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"message": "Record deleted successfully"}
