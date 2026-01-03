import logging
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

from routers.auth import get_current_user
from database_models import User
from ..services.piper_client import piper_tts, TTSConnectionError

# Setup logging
logger = logging.getLogger(__name__)

# Create a new router for admin endpoints
router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    responses={403: {"description": "Operation not permitted"}},
)

# --- Pydantic Models ---
class TtsTestRequest(BaseModel):
    text: str
    language: str = "en"
    speed: float = 1.0
    silence: float = 0.0

# --- Dependency for Admin User ---
async def get_admin_user(current_user: User = Depends(get_current_user)):
    """
    Dependency that checks if the current user is an admin.
    If not, it raises a 403 Forbidden error.
    """
    if not current_user or not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="You do not have permission to access this resource.")
    return current_user

# --- TTS Test Endpoint ---
@router.post("/tts/test", dependencies=[Depends(get_admin_user)])
async def test_tts(request: TtsTestRequest):
    """
    Allows admins to test the Piper TTS service with custom text and settings.
    Streams back a WAV audio file.
    """
    try:
        audio_bytes = await piper_tts.generate_audio(
            text=request.text,
            language=request.language,
            speed=request.speed,
            silence=request.silence
        )
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="TTS generation failed, received no audio data.")

        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")
    except TTSConnectionError as e:
        raise HTTPException(status_code=503, detail=f"TTS Service Unavailable: {e}")
    except Exception as e:
        logger.error(f"Error in TTS test endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Database Viewer for job_state.db ---
DB_PATH = "job_state.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed.")

@router.get("/db/job_state/tables", dependencies=[Depends(get_admin_user)])
async def get_job_state_db_tables():
    """
    Returns a list of table names from the job_state.db SQLite database.
    Only accessible by admin users.
    """
    tables = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        rows = cursor.fetchall()
        tables = [row['name'] for row in rows]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to query database tables: {e}")
    finally:
        if conn:
            conn.close()
    return {"tables": tables}

@router.get("/db/job_state/table/{table_name}", dependencies=[Depends(get_admin_user)])
async def get_job_state_db_table_content(table_name: str):
    """
    Returns the content of a specified table from the job_state.db SQLite database.
    Performs a security check on the table name to prevent SQL injection.
    Only accessible by admin users.
    """
    # Security First: Validate table_name against a fetched list of actual tables
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        valid_tables = [row['name'] for row in cursor.fetchall()]
        
        if table_name not in valid_tables:
            raise HTTPException(status_code=400, detail=f"Invalid table name: {table_name}")

        # Now that the table name is validated, it's safe to use it in the query
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY created_at DESC;")
        rows = cursor.fetchall()
        content = [dict(row) for row in rows]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to query table content: {e}")
    finally:
        if conn:
            conn.close()
    return {"table_name": table_name, "content": content}
