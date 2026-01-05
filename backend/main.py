import os
import uuid
import asyncio
import time
import mimetypes
import io
import re
import json
import zipfile
import logging
import hashlib
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from fastapi import BackgroundTasks as BackgroundTasksExplicit
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Import the new, clean refactored modules
from database import initialize_database
from routers.auth import router as auth_router, get_current_user
from routers.admin import router as admin_router
from routers.upload import router as upload_router
from core.setup import create_admin_user
from database_models import User, StoryOperations
from services.story_service import GeminiService
from services.tts_service import kokoro_tts
from services.hash_service import hash_service
from job_state import job_manager
from story_storage import storage_manager, cleanup_scheduler_task, database_cleanup_scheduler_task
from typing import Optional, TYPE_CHECKING, Dict, Any

# Type checking imports for Pylance
if TYPE_CHECKING:
    from services.story_service import GeminiService

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- App Initialization ---
app = FastAPI(title="EduStory API")

# Add CORS middleware to allow requests from any origin.
# For production, you would want to restrict this to your frontend's domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Background Tasks ---
# Note: Old cleanup system removed. Now using story_storage.py with 24-hour TTL cleanup

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """
    This function runs when the application starts.
    It initializes the database and starts background tasks.
    """
    # Skip database operations in development mode
    if os.getenv("ENV") == "development":
        logger.info("✓ Development mode: Skipping database initialization")
        logger.info("✓ Development mode: Skipping admin user creation")
    else:
        try:
            logger.info("Initializing database...")
            initialize_database()
            logger.info("Database initialization successful.")
            
            logger.info("Performing initial user setup (admin check)...")
            create_admin_user()
            logger.info("Initial user setup complete.")
            
        except Exception as e:
            logger.critical(f"FATAL: Could not initialize database on startup. Error: {e}")
            # In a real app, you might want the app to fail fast if the DB is unavailable.
    
    logger.info("Initializing story storage manager...")
    # Storage manager auto-initializes on import
    
    logger.info("Starting story cleanup scheduler (24-hour TTL)...")
    asyncio.create_task(cleanup_scheduler_task())
    
    # Skip database cleanup in development mode
    if os.getenv("ENV") != "development":
        logger.info("Starting database cleanup scheduler (runs every 2 days)...")
        asyncio.create_task(database_cleanup_scheduler_task())
    else:
        logger.info("✓ Development mode: Skipping database cleanup scheduler")


# --- API Routers ---
# Include the new authentication router, which contains /signup, /token, /me
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(upload_router)


# --- Non-Auth related application logic ---

# Type annotation for gemini service to help Pylance
from typing import Dict, Any, List, TYPE_CHECKING

# Explicitly declare the methods Pylance should recognize
# This helps with static analysis while maintaining runtime functionality
gemini: 'GeminiService' = GeminiService()
jobs: Dict[str, Any] = {}

# Method existence hints for Pylance (these don't affect runtime)
# Pylance will recognize these methods exist on the gemini instance
if False:
    # These are never executed but help Pylance understand the types
    _ = gemini.process_file_to_story
    _ = gemini.generate_image
    _ = gemini._extract_json_from_response
    _ = gemini._exponential_backoff
    _ = gemini._call_with_exponential_backoff

# Note: generated_stories and saved_stories directories created by storage_manager
# Keeping uploads folder for backward compatibility during migration
os.makedirs("uploads", exist_ok=True)

mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('image/png', '.png')

# --- Static File Serving ---
# Old outputs directory kept temporarily for backward compatibility
if os.path.exists("outputs"):
    app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

# Mount generated_stories for temporary/in-progress stories
app.mount("/api/generated-stories", StaticFiles(directory="generated_stories"), name="generated_stories")

# Custom endpoint handles saved-stories with UUID prefix matching (see below)
# app.mount("/api/saved-stories", StaticFiles(directory="saved_stories"), name="saved_stories")

@app.api_route("/api/saved-stories/{story_id}/{filename:path}", methods=["GET", "HEAD"])
async def serve_story_file(story_id: str, filename: str):
    """
    Serve story files with smart UUID prefix matching.
    Handles both GET and HEAD requests.
    If the exact filename doesn't exist, search for files with UUID prefix.
    """
    import glob
    import os
    from pathlib import Path
    from fastapi.responses import FileResponse
    
    logger.info(f"📁 File request: story_id={story_id}, filename={filename}")
    
    story_dir = Path("saved_stories") / story_id
    logger.info(f"📂 Looking in directory: {story_dir}")
    
    if not story_dir.exists():
        logger.error(f"❌ Story directory does not exist: {story_dir}")
        raise HTTPException(status_code=404, detail=f"Story directory not found: {story_id}")
    
    exact_path = story_dir / filename
    logger.info(f"🔍 Checking exact path: {exact_path}")
    
    # Try exact match first
    if exact_path.exists() and exact_path.is_file():
        logger.info(f"✅ Found exact match: {exact_path}")
        return FileResponse(exact_path)
    
    # If not found, try to find file with UUID prefix (e.g., uuid_scene_0.png)
    # Extract the base filename without UUID
    pattern = str(story_dir / f"*_{filename}")
    logger.info(f"🔎 Searching with glob pattern: {pattern}")
    matches = glob.glob(pattern)
    logger.info(f"📋 Glob matches: {matches}")
    
    if matches:
        logger.info(f"✅ Found UUID-prefixed file: {matches[0]}")
        return FileResponse(matches[0])
    
    # Try without underscore separator (in case files are stored differently)
    pattern2 = str(story_dir / f"*{filename}")
    logger.info(f"🔎 Trying alternative pattern: {pattern2}")
    matches2 = glob.glob(pattern2)
    logger.info(f"📋 Alternative matches: {matches2}")
    
    if matches2:
        logger.info(f"✅ Found file with alternative pattern: {matches2[0]}")
        return FileResponse(matches2[0])
    
    # List all files in directory for debugging
    all_files = list(story_dir.iterdir())
    logger.error(f"❌ File not found. Available files: {[f.name for f in all_files]}")
    raise HTTPException(status_code=404, detail=f"File not found: {filename}")

@app.api_route("/api/generated-stories/{story_id}/{filename:path}", methods=["GET", "HEAD"])
async def serve_generated_story_file(story_id: str, filename: str):
    """
    Serve files from generated_stories folder.
    Similar to saved-stories endpoint but for in-progress/temporary stories.
    """
    import glob
    import os
    from pathlib import Path
    from fastapi.responses import FileResponse
    
    logger.info(f"📁 Generated story file request: story_id={story_id}, filename={filename}")
    
    story_dir = Path("generated_stories") / story_id
    logger.info(f"📂 Looking in directory: {story_dir}")
    
    if not story_dir.exists():
        logger.error(f"❌ Generated story directory does not exist: {story_dir}")
        raise HTTPException(status_code=404, detail=f"Generated story directory not found: {story_id}")
    
    exact_path = story_dir / filename
    logger.info(f"🔍 Checking exact path: {exact_path}")
    
    # Try exact match first
    if exact_path.exists() and exact_path.is_file():
        logger.info(f"✅ Found exact match: {exact_path}")
        return FileResponse(exact_path)
    
    # List all files in directory for debugging
    all_files = list(story_dir.iterdir())
    logger.error(f"❌ File not found. Available files: {[f.name for f in all_files]}")
    raise HTTPException(status_code=404, detail=f"File not found: {filename}")

app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

def _safe_story_dirname(story_name: str, story_id: str) -> str:
    """Create a filesystem-friendly folder name; fallback to ID fragment on collision/empty."""
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", story_name.strip().lower()) if story_name else ""
    slug = slug.strip("-") or f"story-{story_id[:8]}"
    if os.path.exists(os.path.join("saved_stories", slug)):
        slug = f"{slug}-{story_id[:8]}"
    return slug

@app.get("/api/avatars")
async def get_avatars() -> List[Dict[str, str]]:
    return [
        {"id": "wizard", "name": "Professor Paws", "description": "Wise teacher."},
        {"id": "robot", "name": "Robo-Buddy", "description": "Tech explorer."},
        {"id": "dinosaur", "name": "Dino-Explorer", "description": "Nature guide."}
    ]

async def generate_scene_media_progressive(story_id: str, scene_id: str, scene_index: int, scene: dict, voice: str, speed: float, story_seed: int, is_mobile: bool = False):
    """
    Generate image and audio for a scene IN PARALLEL with mobile optimization.
    Updates job state as each completes.
    """
    character_prompt = scene.get("image_prompt", "")
    text = scene.get("narrative_text", "")
    
    async def generate_image():
        try:
            if not character_prompt:
                job_manager.update_scene_image(scene_id, "skipped")
                return
            
            job_manager.update_scene_image(scene_id, "processing")
            
            # Use mobile-optimized image generation for mobile devices
            if is_mobile:
                img_bytes = await asyncio.to_thread(
                    gemini.generate_image_mobile_optimized,
                    character_prompt,
                    text,
                    story_seed,
                    True  # is_mobile=True
                )
            else:
                img_bytes = await asyncio.to_thread(
                    gemini.generate_image,
                    character_prompt,
                    text,
                    story_seed
                )
            
            if img_bytes:
                img_name = f"scene_{scene_index}.png"
                # Use new storage manager
                try:
                    img_url = storage_manager.save_file(story_id, img_name, img_bytes, in_saved=False)
                    job_manager.update_scene_image(scene_id, "completed", img_url)
                    logger.info(f"✓ Scene {scene_index} image complete ({'mobile' if is_mobile else 'desktop'}): {img_url}")
                except Exception as save_error:
                    logger.error(f"Failed to save image: {save_error}")
                    job_manager.update_scene_image(scene_id, "failed")
            else:
                job_manager.update_scene_image(scene_id, "failed")
                logger.error(f"✗ Scene {scene_index} image failed")
        except Exception as e:
            logger.error(f"✗ Scene {scene_index} image error: {e}")
            job_manager.update_scene_image(scene_id, "failed")
    
    async def generate_audio():
        try:
            if not text:
                job_manager.update_scene_audio(scene_id, "skipped")
                return
            
            job_manager.update_scene_audio(scene_id, "processing")
            
            # Use mobile-optimized audio for mobile devices
            from services.chatterbox_client import chatterbox
            if is_mobile:
                audio_bytes = await chatterbox.generate_audio_optimized(text, voice, True)
            else:
                audio_bytes = await kokoro_tts.generate_audio(text, voice, speed)
            
            if audio_bytes:
                aud_name = f"scene_{scene_index}.wav"  # Kokoro provides WAV audio
                # Use new storage manager
                try:
                    aud_url = storage_manager.save_file(story_id, aud_name, audio_bytes, in_saved=False)
                    job_manager.update_scene_audio(scene_id, "completed", aud_url)
                    logger.info(f"✓ Scene {scene_index} audio complete ({'mobile' if is_mobile else 'desktop'}): {aud_url}")
                except Exception as save_error:
                    logger.error(f"Failed to save audio: {save_error}")
                    job_manager.update_scene_audio(scene_id, "failed")
            else:
                job_manager.update_scene_audio(scene_id, "failed")
                logger.error(f"✗ Scene {scene_index} audio failed")
        except Exception as e:
            logger.error(f"✗ Scene {scene_index} audio error: {e}")
            job_manager.update_scene_audio(scene_id, "failed")
    
    # Run image and audio generation IN PARALLEL
    await asyncio.gather(generate_image(), generate_audio())

async def run_ai_workflow_progressive_mobile(story_id: str, file_path: str, grade_level: str, voice: str, speed: float, is_mobile: bool):
    """
    Progressive story generation workflow:
    1. Create story folder in generated_stories
    2. Generate story structure
    3. Create scene records immediately
    4. Process scenes in parallel (images + audio per scene)
    """
    try:
        # Create story folder with metadata
        storage_manager.create_story_folder(story_id, {
            "grade_level": grade_level,
            "voice": voice,
            "speed": speed,
            "file_path": file_path
        })
        logger.info(f"📁 Created story folder: generated_stories/{story_id}")
        
        # Generate story structure
        story_data = await asyncio.to_thread(gemini.process_file_to_story, file_path, grade_level)
        
        if not story_data:
            raise Exception("AI failed to generate story content.")
        
        scenes = story_data.get("scenes", [])
        title = story_data.get("title", "Untitled Story")
        
        # Initialize job state
        job_manager.update_story_metadata(story_id, title, len(scenes))
        
        # Create scene records immediately (text is ready)
        scene_ids = []
        for i, scene in enumerate(scenes):
            scene_id = job_manager.create_scene(
                story_id, 
                i, 
                scene.get("narrative_text", ""),
                scene.get("image_prompt", "")
            )
            scene_ids.append(scene_id)
        
        logger.info(f"✓ Story structure ready: {len(scenes)} scenes")
        
        # --- Hybrid Generation Strategy ---
        story_seed = int(uuid.uuid4().hex[:8], 16)
        
        # 1. Generate Scene 1 first for a fast user start
        if len(scenes) > 0:
            logger.info("Starting media generation for Scene 1 (priority)...")
            await generate_scene_media_progressive(
                story_id, scene_ids[0], 0, scenes[0], voice, speed, story_seed
            )
            logger.info("✓ Finished media generation for Scene 1.")

        # 2. Generate the rest of the scenes in parallel
        if len(scenes) > 1:
            logger.info(f"Starting parallel media generation for remaining {len(scenes) - 1} scenes...")
            remaining_tasks = [
                generate_scene_media_progressive(story_id, scene_ids[i], i, scene, voice, speed, story_seed)
                for i, scene in enumerate(scenes[1:], start=1) # Start enumeration from index 1
            ]
            await asyncio.gather(*remaining_tasks, return_exceptions=True)
            logger.info("✓ Finished parallel generation for remaining scenes.")

        logger.info(f"✓ All media generation complete for story {story_id}")
        
    except Exception as e:
        logger.error(f"AI Workflow Error: {e}")
        job_manager.mark_story_failed(story_id, str(e))

@app.post("/api/check-duplicate")
async def check_duplicate(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Check if a file has been uploaded across both saved and generated stories."""
    # Read file content
    file_content = await file.read()
    
    # Use hash service to find duplicates
    duplicate_info = hash_service.find_duplicate(file_content, file.filename)
    
    # Reset file pointer for potential reuse
    await file.seek(0)
    
    if duplicate_info:
        # Check if duplicate is in saved_stories (persistent) or generated_stories (temp)
        saved_matches = duplicate_info.get("saved_stories", [])
        generated_matches = duplicate_info.get("generated_stories", [])
        
        # Prefer saved stories as they are permanent
        if saved_matches:
            match = saved_matches[0]
            return {
                "is_duplicate": True,
                "duplicate_type": "saved",
                "story_id": match["story_id"],
                "story_title": match.get("metadata", {}).get("title", "Unknown"),
                "created_at": match.get("metadata", {}).get("created_timestamp"),
                "file_hash": duplicate_info["hash"]
            }
        elif generated_matches:
            match = generated_matches[0]
            return {
                "is_duplicate": True,
                "duplicate_type": "generated",
                "story_id": match["story_id"],
                "story_title": match.get("metadata", {}).get("title", "Unknown"),
                "created_at": match.get("metadata", {}).get("created_timestamp"),
                "file_hash": duplicate_info["hash"]
            }
    
    return {"is_duplicate": False, "file_hash": hash_service.generate_bytes_hash(file_content)}

@app.post("/api/upload")
async def upload_story(
    background_tasks: BackgroundTasksExplicit,  # type: ignore
    file: UploadFile = File(...), 
    grade_level: str = Form("Grade 4"), 
    voice: str = Form("af_sarah"), 
    speed: float = Form(1.0),
    file_hash: str = Form(None),
    force_new: bool = Form(False),
    user_agent: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Upload file and handle duplicate detection.
    If duplicate found and user chooses to view existing, delete temp story and redirect.
    If duplicate found and user chooses to generate new, create new story with copy of file.
    """
    # Read file content
    file_content = await file.read()
    
    # Calculate hash if not provided
    if not file_hash:
        file_hash = hash_service.generate_bytes_hash(file_content)
    
    # Check for duplicate unless force_new is True
    duplicate_info = None
    if not force_new:
        duplicate_info = hash_service.find_duplicate(file_content, file.filename)
    
    if duplicate_info:
        saved_matches = duplicate_info.get("saved_stories", [])
        generated_matches = duplicate_info.get("generated_stories", [])
        
        # Return duplicate info - frontend will handle user choice
        if saved_matches or generated_matches:
            match = (saved_matches[0] if saved_matches else generated_matches[0])
            duplicate_type = "saved" if saved_matches else "generated"
            
            return {
                "is_duplicate": True,
                "duplicate_type": duplicate_type,
                "story_id": match["story_id"],
                "story_title": match.get("metadata", {}).get("title", "Unknown"),
                "created_at": match.get("metadata", {}).get("created_timestamp"),
                "file_hash": file_hash,
                "message": "File already exists. Choose to view existing or generate new."
            }
    
    # No duplicate or force_new=True - create new story
    story_id = str(uuid.uuid4())
    
    # Create temporary story folder in generated_stories
    temp_dir = storage_manager.create_story_folder(story_id, {
        "grade_level": grade_level,
        "voice": voice,
        "speed": speed,
        "original_filename": file.filename,
        "file_hash": file_hash,
        "user_id": current_user['id'],
        "username": current_user['username'],
        "is_temp": True
    })
    
    # Save original file to temp folder
    filename = file.filename or "uploaded_file"
    temp_file_path = os.path.join(temp_dir, filename)
    with open(temp_file_path, "wb") as f:
        f.write(file_content)
    
    # Store file hash in metadata
    hash_service.update_story_metadata_hash(story_id, file_hash, in_saved=False)
    
    # Initialize job state
    job_manager.initialize_story(
        story_id, 
        grade_level, 
        file_hash=file_hash, 
        user_id=current_user['id'], 
        username=current_user['username']
    )
    
    # Detect if user is on mobile device
    is_mobile = False
    if user_agent:
        mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'windows phone', 'blackberry']
        is_mobile = any(keyword in user_agent.lower() for keyword in mobile_keywords)
    
    # Use progressive workflow with mobile optimization
    background_tasks.add_task(
        run_ai_workflow_progressive_mobile, 
        story_id, 
        temp_file_path, 
        grade_level, 
        voice, 
        speed, 
        is_mobile
    )
    
    return {
        "job_id": story_id, 
        "is_mobile": is_mobile,
        "message": "Story generation started"
    }

@app.post("/api/handle-duplicate-choice")
async def handle_duplicate_choice(
    background_tasks: BackgroundTasks,
    choice: str = Form(...),  # "view_existing" or "generate_new"
    duplicate_story_id: str = Form(...),
    duplicate_type: str = Form(...),  # "saved" or "generated"
    file: UploadFile = File(...),
    grade_level: str = Form("Grade 4"),
    voice: str = Form("af_sarah"),
    speed: float = Form(1.0),
    user_agent: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Handle user's choice when duplicate is detected.
    - view_existing: Delete temp story and return existing story_id
    - generate_new: Create new story with file copy
    """
    if choice == "view_existing":
        # Delete any temp story that was created
        if duplicate_type == "generated":
            # This is a temp story, delete it
            storage_manager.delete_story(duplicate_story_id, in_saved=False)
            job_manager.mark_story_failed(duplicate_story_id, "User chose to view existing story")
        
        return {
            "action": "view_existing",
            "story_id": duplicate_story_id,
            "message": "Redirecting to existing story"
        }
    
    elif choice == "generate_new":
        # Create new story with fresh UUID
        new_story_id = str(uuid.uuid4())
        
        # Read file content
        file_content = await file.read()
        
        # Create new temp story folder
        temp_dir = storage_manager.create_story_folder(new_story_id, {
            "grade_level": grade_level,
            "voice": voice,
            "speed": speed,
            "original_filename": file.filename,
            "file_hash": hash_service.generate_bytes_hash(file_content),
            "user_id": current_user['id'],
            "username": current_user['username'],
            "is_temp": True,
            "note": "Generated despite duplicate - user choice"
        })
        
        # Save file to new temp folder
        filename = file.filename or "uploaded_file"
        temp_file_path = os.path.join(temp_dir, filename)
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        
        # Initialize job state
        job_manager.initialize_story(
            new_story_id, 
            grade_level, 
            file_hash=hash_service.generate_bytes_hash(file_content), 
            user_id=current_user['id'], 
            username=current_user['username']
        )
        
        # Detect mobile
        is_mobile = False
        if user_agent:
            mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'windows phone', 'blackberry']
            is_mobile = any(keyword in user_agent.lower() for keyword in mobile_keywords)
        
        # Start generation
        background_tasks.add_task(
            run_ai_workflow_progressive_mobile, 
            new_story_id, 
            temp_file_path, 
            grade_level, 
            voice, 
            speed, 
            is_mobile
        )
        
        return {
            "action": "generate_new",
            "job_id": new_story_id,
            "message": "New story generation started"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid choice")


# Progressive endpoints for scene-by-scene loading
@app.get("/api/story/{story_id}/status")
async def get_story_status(story_id: str) -> Dict[str, Any]:
    """Get overall story status with scene completion info."""
    logger.info(f"🔍 Getting story status for: {story_id}")
    
    # First check if story is in the active job system
    status = job_manager.get_story_status(story_id)
    if status:
        logger.info(f"✅ Found story in job manager")
        scenes = job_manager.get_all_scenes(story_id)
        return {
            "story_id": story_id,
            "status": status["status"],
            "title": status["title"],
            "total_scenes": status["total_scenes"],
            "completed_scenes": status["completed_scenes"],
            "scenes": [
                {
                    "scene_index": s["scene_index"],
                    "text": s["text"],
                    "image_status": s["image_status"],
                    "audio_status": s["audio_status"],
                    "image_url": s["image_url"],
                    "audio_url": s["audio_url"]
                }
                for s in scenes
            ]
        }
    
    # If not in job system, check if it's a saved story
    logger.info(f"📂 Not in job manager, checking saved stories...")
    try:
        story_exists = storage_manager.story_exists(story_id, in_saved=True)
        logger.info(f"📂 Story exists in saved: {story_exists}")
        
        if story_exists:
            # This is a saved story - reconstruct from directory
            metadata = storage_manager.get_metadata(story_id, in_saved=True)
            logger.info(f"📋 Metadata: {metadata}")
            
            # Try to load from story.json if it exists
            story_path = storage_manager.get_story_path(story_id, in_saved=True)
            logger.info(f"📁 Story path: {story_path}")
            
            story_json_path = os.path.join(story_path, "story.json")
            logger.info(f"📄 Checking for story.json at: {story_json_path}")
            logger.info(f"📄 story.json exists: {os.path.exists(story_json_path)}")
            
            if os.path.exists(story_json_path):
                logger.info(f"✅ Loading from story.json")
                with open(story_json_path, 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                    logger.info(f"📊 Loaded story data with {len(story_data.get('scenes', []))} scenes")
                    
                return {
                    "story_id": story_id,
                    "status": "completed",
                    "title": story_data.get("title", metadata.get("title", "Saved Story")),
                    "total_scenes": len(story_data.get("scenes", [])),
                    "completed_scenes": len(story_data.get("scenes", [])),
                    "scenes": [
                        {
                            "scene_index": idx,
                            "text": scene.get("text", ""),
                            "image_status": "completed",
                            "audio_status": "completed",
                            "image_url": scene.get("imageUrl") or scene.get("image_url", ""),
                            "audio_url": scene.get("audioUrl") or scene.get("audio_url", "")
                        }
                        for idx, scene in enumerate(story_data.get("scenes", []))
                    ]
                }
            else:
                # No story.json, try to reconstruct from files
                logger.warning(f"⚠️ No story.json found, reconstructing from files")
                story_dir = storage_manager.get_story_path(story_id, in_saved=True)
                logger.info(f"📁 Scanning directory: {story_dir}")
                
                # List all files in directory
                if os.path.exists(story_dir):
                    all_files = os.listdir(story_dir)
                    logger.info(f"📂 Files in directory: {all_files}")
                else:
                    logger.error(f"❌ Story directory does not exist: {story_dir}")
                
                scenes = []
                scene_index = 0
                
                # Look for scene files (scene_0.png, scene_0.wav, etc.)
                while True:
                    image_file = f"scene_{scene_index}.png"
                    audio_file = f"scene_{scene_index}.wav"
                    
                    image_path = os.path.join(story_dir, image_file)
                    audio_path = os.path.join(story_dir, audio_file)
                    
                    logger.info(f"🔍 Looking for scene {scene_index}: image={os.path.exists(image_path)}, audio={os.path.exists(audio_path)}")
                    
                    if not (os.path.exists(image_path) or os.path.exists(audio_path)):
                        break
                    
                    scenes.append({
                        "scene_index": scene_index,
                        "text": "",  # No text available without story.json
                        "image_status": "completed" if os.path.exists(image_path) else "missing",
                        "audio_status": "completed" if os.path.exists(audio_path) else "missing",
                        "image_url": f"/api/saved-stories/{story_id}/{image_file}" if os.path.exists(image_path) else "",
                        "audio_url": f"/api/saved-stories/{story_id}/{audio_file}" if os.path.exists(audio_path) else ""
                    })
                    scene_index += 1
                
                logger.info(f"✅ Reconstructed {len(scenes)} scenes from files")
                
                return {
                    "story_id": story_id,
                    "status": "completed",
                    "title": metadata.get("title", "Saved Story"),
                    "total_scenes": len(scenes),
                    "completed_scenes": len(scenes),
                    "scenes": scenes
                }
    except Exception as e:
        logger.error(f"❌ Error loading saved story {story_id}: {e}")
        logger.exception(e)
    
    # Story not found in either system
    raise HTTPException(status_code=404, detail="Story not found")


@app.get("/api/story/{story_id}/scene/{scene_index}")
async def get_scene_status(story_id: str, scene_index: int) -> Dict[str, Any]:
    """Get specific scene data."""
    scene_id = f"{story_id}_scene_{scene_index}"
    scene = job_manager.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    return {
        "scene_index": scene["scene_index"],
        "text": scene["text"],
        "image_status": scene["image_status"],
        "audio_status": scene["audio_status"],
        "image_url": scene["image_url"],
        "audio_url": scene["audio_url"]
    }


@app.get("/api/status/{job_id}")
async def get_status(job_id: str) -> Dict[str, Any]:
    # Check if it's a progressive story
    status = job_manager.get_story_status(job_id)
    if status:
        scenes = job_manager.get_all_scenes(job_id)
        # Filter to only include completed scenes (both image and audio ready)
        completed_scenes = [
            {
                "text": s["text"],
                "image_url": s["image_url"],
                "audio_url": s["audio_url"]
            }
            for s in scenes
            if s["image_status"] == "completed" and s["audio_status"] == "completed"
        ]
        
        # Calculate real progress based on completed scenes
        actual_progress = int((len(completed_scenes) / status["total_scenes"]) * 100) if status["total_scenes"] > 0 else 0
        
        return {
            "status": status["status"],
            "progress": actual_progress,
            "total_scenes": status["total_scenes"],  # Always include total count
            "completed_scene_count": len(completed_scenes),  # Number of completed scenes
            "result": {
                "title": status["title"],
                "scenes": completed_scenes,
                "quiz": status.get("quiz", [])
            }
        }
    
    # Fall back to old job system
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.post("/api/save-story/{job_id}")
async def save_story(job_id: str, story_name: str = Form(...), user: User = Depends(get_current_user)):
    """
    Saves a generated story to the database, associating it with the current user.
    This also moves the story's assets from temporary storage to permanent storage.
    """
    # Check if it's a progressive story
    status = job_manager.get_story_status(job_id)
    if status and status["status"] == "completed":
        # Progressive story system - move folder from generated_stories to saved_stories
        saved_story_id = str(uuid.uuid4())
        scenes = job_manager.get_all_scenes(job_id)
        
        # Move the entire folder from generated_stories to saved_stories
        try:
            storage_manager.move_to_saved(job_id, saved_story_id)
            logger.info(f"✅ Moved story folder: {job_id} -> saved_stories/{saved_story_id}")
        except Exception as move_error:
            logger.error(f"Failed to move story folder: {move_error}")
            raise HTTPException(status_code=500, detail=f"Failed to move story files: {move_error}")
        
        # Update URLs from generated-stories to saved-stories
        updated_scenes = []
        for idx, s in enumerate(scenes):
            scene_data = {
                "text": s["text"],
                "image_url": s.get("image_url", ""),
                "audio_url": s.get("audio_url", "")
            }
            
            # Update image URL
            if scene_data["image_url"]:
                scene_data["image_url"] = scene_data["image_url"].replace(
                    f"/api/generated-stories/{job_id}/",
                    f"/api/saved-stories/{saved_story_id}/"
                )
            
            # Update audio URL
            if scene_data["audio_url"]:
                scene_data["audio_url"] = scene_data["audio_url"].replace(
                    f"/api/generated-stories/{job_id}/",
                    f"/api/saved-stories/{saved_story_id}/"
                )
            
            updated_scenes.append(scene_data)
        
        story_data = {
            "title": status["title"],
            "scenes": updated_scenes,
            "quiz": status.get("quiz", [])
        }
        
        success = StoryOperations.save_story(
            user_id=user['id'],
            story_id=saved_story_id,
            name=story_name,
            story_data=story_data
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save story to the database.")
        
        logger.info(f"Story {saved_story_id} saved successfully with {len(updated_scenes)} scenes")
        return {"story_id": saved_story_id, "message": "Story saved successfully"}
    
    # Fall back to old system
    if job_id not in jobs or jobs[job_id].get("status") != "completed":
        raise HTTPException(status_code=404, detail="Story generation job not found or not completed.")
    
    try:
        story_data = jobs[job_id]["result"]
        # Generate a new, permanent ID for the story.
        story_id = str(uuid.uuid4())
        
        # Save story to the database, associated with the user
        success = StoryOperations.save_story(
            user_id=user['id'],
            story_id=story_id,
            name=story_name,
            story_data=story_data
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save story to the database.")

        # --- File System Operations ---
        # Create a safe directory name for the story assets
        folder_name = _safe_story_dirname(story_name, story_id)
        story_dir = os.path.join("saved_stories", folder_name)
        os.makedirs(story_dir, exist_ok=True)

        # Move the original uploaded document, if it exists
        upload_path = jobs[job_id].get("upload_path")
        if upload_path and os.path.exists(upload_path):
            upload_filename = os.path.basename(upload_path).replace(f"{job_id}_", "", 1)
            import shutil
            shutil.move(upload_path, os.path.join(story_dir, upload_filename))
        
        # Move all generated media (images, audio) for this job
        for filename in os.listdir("outputs"):
            if filename.startswith(job_id):
                import shutil
                shutil.move(os.path.join("outputs", filename), os.path.join(story_dir, filename.replace(f"{job_id}_", "", 1)))
        
        # We don't save metadata to a JSON file anymore since it's in the DB.
        
        # Clean up the in-memory job
        del jobs[job_id]

        return {"story_id": story_id, "message": "Story saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save story for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while saving the story.")

@app.get("/api/list-stories")
async def list_stories(user: User = Depends(get_current_user)):
    """
    List stories. Admins see all stories, regular users see only their own.
    """
    try:
        logger.info(f"User requesting stories - ID: {user.get('id')}, Email: {user.get('email')}, Is Admin: {user.get('is_admin')}")
        if user.get('is_admin'):
            logger.info(f"Admin user - fetching all stories")
            stories = StoryOperations.get_all_stories()
            logger.info(f"Admin retrieved {len(stories)} stories")
        else:
            logger.info(f"Regular user - fetching only their stories")
            stories = StoryOperations.get_user_stories(user['id'])
            logger.info(f"User retrieved {len(stories)} stories")
        return stories
    except Exception as e:
        logger.error(f"Failed to list stories: {e}")
        raise HTTPException(status_code=500, detail="Failed to list stories.")

@app.get("/api/load-story/{story_id}")
async def load_story(story_id: str, user: User = Depends(get_current_user)):
    """
    Load a specific story. Enforces ownership rules (users can only load their own
    stories, unless they are an admin).
    """
    logger.info(f"Loading story {story_id} for user {user.get('email')} (admin: {user.get('is_admin')})")
    story = StoryOperations.get_story(story_id, user)
    if not story:
        logger.warning(f"Story {story_id} not found or user {user.get('email')} lacks permission")
        raise HTTPException(status_code=404, detail="Story not found or you do not have permission to view it.")
    
    logger.info(f"Successfully loaded story {story_id}: {story.get('name')}")
    # The 'story_data' from the DB needs to have its URLs updated to point to the correct static path
    story_data = story.get("story_data", {})
    
    # Log scenes info for debugging
    scenes = story_data.get("scenes", [])
    logger.info(f"Story has {len(scenes)} scenes")
    
    for idx, scene in enumerate(scenes):
        # Log original URLs
        orig_image = scene.get("image_url", "")
        orig_audio = scene.get("audio_url", "")
        logger.debug(f"Scene {idx} original - image: {orig_image[:50] if orig_image else 'EMPTY'}, audio: {orig_audio[:50] if orig_audio else 'EMPTY'}")
        
        if scene.get("image_url"):
            scene["image_url"] = scene["image_url"].replace("/api/outputs/", f"/api/saved-stories/{story_id}/")
        else:
            logger.warning(f"Scene {idx} has no image_url!")
            
        if scene.get("audio_url"):
            scene["audio_url"] = scene["audio_url"].replace("/api/outputs/", f"/api/saved-stories/{story_id}/")
        else:
            logger.warning(f"Scene {idx} has no audio_url!")
            
    return {"name": story["name"], "story_data": story_data}

@app.delete("/api/delete-story/{story_id}")
async def delete_story(story_id: str, user: User = Depends(get_current_user)):
    """
    Deletes a specific story. Enforces ownership (users can only delete their own
    stories, unless they are an admin).
    """
    # The StoryOperations.delete_story now handles the permission logic.
    was_deleted = StoryOperations.delete_story(story_id, user)
    
    if not was_deleted:
        raise HTTPException(status_code=404, detail="Story not found or you do not have permission to delete it.")
        
    # Also delete the story from the file system
    story_dir = os.path.join("saved_stories", story_id)
    if os.path.exists(story_dir):
        import shutil
        shutil.rmtree(story_dir)

    return {"message": "Story deleted successfully"}

@app.get("/api/export-job/{job_id}")
async def export_job(job_id: str):
    """
    Export a job (story generation) as a ZIP file for offline use.
    Includes all scenes with images and audio files.
    """
    # Check if it's a progressive story
    status = job_manager.get_story_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    scenes = job_manager.get_all_scenes(job_id)
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add story metadata
        story_data = {
            "title": status["title"],
            "scenes": []
        }
        
        # Add each scene's assets
        for idx, scene in enumerate(scenes):
            scene_data = {
                "text": scene["text"],
                "image_url": f"scene_{idx}.png",
                "audio_url": f"scene_{idx}.wav"
            }
            story_data["scenes"].append(scene_data)
            
            # Add image file
            if scene["image_url"]:
                img_path = scene["image_url"].replace("/api/outputs/", "outputs/")
                if os.path.exists(img_path):
                    zip_file.write(img_path, f"scene_{idx}.png")
            
            # Add audio file
            if scene["audio_url"]:
                audio_path = scene["audio_url"].replace("/api/outputs/", "outputs/")
                if os.path.exists(audio_path):
                    zip_file.write(audio_path, f"scene_{idx}.wav")
        
        # Add story.json
        zip_file.writestr("story.json", json.dumps(story_data, indent=2))
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={status['title'].replace(' ', '_')}.zip"
        }
    )

@app.get("/api/export-story/{story_id}")
async def export_story(story_id: str, user: User = Depends(get_current_user)):
    """
    Export a saved story as a ZIP file for offline use.
    Includes all scenes with images and audio files.
    """
    story = StoryOperations.get_story(story_id, user)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found or you do not have permission to access it.")
    
    story_data = story.get("story_data", {})
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Update story data with local file references
        export_data = {
            "title": story_data.get("title", story["name"]),
            "scenes": []
        }
        
        # Add each scene's assets
        for idx, scene in enumerate(story_data.get("scenes", [])):
            scene_data = {
                "text": scene.get("text", ""),
                "image_url": f"scene_{idx}.png",
                "audio_url": f"scene_{idx}.wav"
            }
            export_data["scenes"].append(scene_data)
            
            # Add image file from saved_stories directory
            if scene.get("image_url"):
                img_path = os.path.join("saved_stories", story_id, f"scene_{idx}.png")
                if os.path.exists(img_path):
                    zip_file.write(img_path, f"scene_{idx}.png")
            
            # Add audio file from saved_stories directory
            if scene.get("audio_url"):
                audio_path = os.path.join("saved_stories", story_id, f"scene_{idx}.wav")
                if os.path.exists(audio_path):
                    zip_file.write(audio_path, f"scene_{idx}.wav")
        
        # Add story.json
        zip_file.writestr("story.json", json.dumps(export_data, indent=2))
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={story['name'].replace(' ', '_')}.zip"
        }
    )
