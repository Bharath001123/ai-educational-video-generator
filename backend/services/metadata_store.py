import sqlite3
from pathlib import Path
import json

# Path to SQLite database file (inside static/generated for easy backup)
DB_PATH = Path(__file__).resolve().parent.parent / "static" / "generated" / "metadata.db"

def _connect():
    """Return a SQLite connection ensuring the DB directory exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the metadata table if it does not exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                duration INTEGER NOT NULL,
                presenter_type TEXT NOT NULL,
                voice TEXT,
                language TEXT,
                file_size INTEGER,
                resolution TEXT,
                thumbnail_path TEXT,
                video_path TEXT NOT NULL,
                subtitle_path TEXT,
                status TEXT
            )
            """
        )
        conn.commit()

def add_record(record: dict):
    """Insert a new video metadata record.

    Expected keys in *record*:
        title, created_at, duration, presenter_type, voice, language,
        file_size, resolution, thumbnail_path, video_path, subtitle_path, status
    """
    init_db()
    columns = [
        "title",
        "created_at",
        "duration",
        "presenter_type",
        "voice",
        "language",
        "file_size",
        "resolution",
        "thumbnail_path",
        "video_path",
        "subtitle_path",
        "status",
    ]
    values = [record.get(col) for col in columns]
    placeholders = ", ".join(["?" for _ in columns])
    with _connect() as conn:
        conn.execute(
            f"INSERT INTO videos ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )
        conn.commit()

def list_records():
    """Return a list of all video records ordered by newest first."""
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM videos ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

def update_thumbnail(record_id: int, thumbnail_path: str):
    """Update the thumbnail_path for a given video record."""
    init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE videos SET thumbnail_path = ? WHERE id = ?",
            (thumbnail_path, record_id),
        )
        conn.commit()


def delete_record(video_id: int):
    """Delete a record by its primary key. Returns *True* if a row was removed."""
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()
        return cur.rowcount > 0
