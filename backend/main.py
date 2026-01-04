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
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
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
from job_state import job_manager
from typing import Optional

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

CLEAN_PATHS = ["outputs", "uploads"]
CLEAN_AGE_SECONDS = 60 * 60  # 1 hour

async def cleanup_old_files():
    """Periodically cleans up old files from temporary directories."""
    now = time.time()
    removed = 0
    logger.info("Running scheduled cleanup of old files...")
    for path in CLEAN_PATHS:
        if not os.path.exists(path):
            continue
        for fname in os.listdir(path):
            fpath = os.path.join(path, fname)
            try:
                if os.path.isfile(fpath) and (now - os.path.getmtime(fpath) > CLEAN_AGE_SECONDS):
                    os.remove(fpath)
                    removed += 1
            except Exception as e:
                logger.warning(f"Could not process file for cleanup '{fpath}': {e}")
    if removed > 0:
        logger.info(f"Cleanup task removed {removed} stale files.")

async def cleanup_scheduler():
    """Scheduler that runs the cleanup task every hour."""
    while True:
        await asyncio.sleep(3600)  # Sleep for 1 hour
        try:
            await cleanup_old_files()
        except Exception as e:
            logger.error(f"Error in cleanup scheduler: {e}")

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """
    This function runs when the application starts.
    It initializes the database and starts background tasks.
    """
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
    
    logger.info("Starting background cleanup task...")
    asyncio.create_task(cleanup_scheduler())


# --- API Routers ---
# Include the new authentication router, which contains /signup, /token, /me
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(upload_router)


# --- Non-Auth related application logic ---

gemini = GeminiService()
jobs = {}

os.makedirs("outputs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("saved_stories", exist_ok=True)

mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('image/png', '.png')

# --- Static File Serving ---
app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")
app.mount("/api/saved-stories", StaticFiles(directory="saved_stories"), name="saved_stories")
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

def _safe_story_dirname(story_name: str, story_id: str) -> str:
    """Create a filesystem-friendly folder name; fallback to ID fragment on collision/empty."""
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", story_name.strip().lower()) if story_name else ""
    slug = slug.strip("-") or f"story-{story_id[:8]}"
    if os.path.exists(os.path.join("saved_stories", slug)):
        slug = f"{slug}-{story_id[:8]}"
    return slug

@app.get("/api/avatars")
async def get_avatars():
    return [
        {"id": "wizard", "name": "Professor Paws", "description": "Wise teacher."},
        {"id": "robot", "name": "Robo-Buddy", "description": "Tech explorer."},
        {"id": "dinosaur", "name": "Dino-Explorer", "description": "Nature guide."}
    ]

async def generate_scene_media_progressive(story_id: str, scene_id: str, scene_index: int, scene: dict, voice: str, speed: float, story_seed: int):
    """
    Generate image and audio for a scene IN PARALLEL.
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
            img_bytes = await asyncio.to_thread(
                gemini.generate_image,
                character_prompt,
                text,
                story_seed
            )
            
            if img_bytes:
                img_name = f"scene_{scene_index}.png"
                img_path = os.path.join("outputs", story_id, img_name)
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
                job_manager.update_scene_image(scene_id, "completed", f"/api/outputs/{story_id}/{img_name}")
                logger.info(f"✓ Scene {scene_index} image complete")
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
            audio_bytes = await kokoro_tts.generate_audio(text, voice, speed)
            
            if audio_bytes:
                aud_name = f"scene_{scene_index}.wav" # Kokoro provides WAV audio
                aud_path = os.path.join("outputs", story_id, aud_name)
                os.makedirs(os.path.dirname(aud_path), exist_ok=True)
                with open(aud_path, "wb") as f:
                    f.write(audio_bytes)
                job_manager.update_scene_audio(scene_id, "completed", f"/api/outputs/{story_id}/{aud_name}")
                logger.info(f"✓ Scene {scene_index} audio complete")
            else:
                job_manager.update_scene_audio(scene_id, "failed")
                logger.error(f"✗ Scene {scene_index} audio failed")
        except Exception as e:
            logger.error(f"✗ Scene {scene_index} audio error: {e}")
            job_manager.update_scene_audio(scene_id, "failed")
    
    # Run image and audio generation IN PARALLEL
    await asyncio.gather(generate_image(), generate_audio())

async def run_ai_workflow_progressive(story_id: str, file_path: str, grade_level: str, voice: str, speed: float):
    """
    Progressive story generation workflow:
    1. Generate story structure
    2. Create scene records immediately
    3. Process scenes in parallel (images + audio per scene)
    """
    try:
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

@app.post("/api/upload")
async def upload_story(background_tasks: BackgroundTasks, file: UploadFile = File(...), grade_level: str = Form("Grade 4"), voice: str = Form("af_sarah"), speed: float = Form(1.0)):
    story_id = str(uuid.uuid4())
    upload_path = os.path.join("uploads", f"{story_id}_{file.filename}")
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    # Immediately create a record for the job to prevent race conditions
    job_manager.initialize_story(story_id, grade_level)
    
    # Use progressive workflow
    background_tasks.add_task(run_ai_workflow_progressive, story_id, upload_path, grade_level, voice, speed)
    return {"job_id": story_id}


# Progressive endpoints for scene-by-scene loading
@app.get("/api/story/{story_id}/status")
async def get_story_status(story_id: str):
    """Get overall story status with scene completion info."""
    status = job_manager.get_story_status(story_id)
    if not status:
        raise HTTPException(status_code=404, detail="Story not found")
    
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


@app.get("/api/story/{story_id}/scene/{scene_index}")
async def get_scene_status(story_id: str, scene_index: int):
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
async def get_status(job_id: str):
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
                "scenes": completed_scenes
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
        # Progressive story system
        story_id = str(uuid.uuid4())
        scenes = job_manager.get_all_scenes(job_id)
        
        # Create permanent storage directory for this story
        story_dir = os.path.join("saved_stories", story_id)
        os.makedirs(story_dir, exist_ok=True)
        logger.info(f"Created story directory: {story_dir}")
        
        # Copy files from outputs to saved_stories and update URLs
        updated_scenes = []
        for s in scenes:
            scene_data = {
                "text": s["text"],
                "image_url": s["image_url"],
                "audio_url": s["audio_url"]
            }
            
            # Copy image file if it exists
            if s.get("image_url") and s["image_url"].startswith("/api/outputs/"):
                old_image_path = s["image_url"].replace("/api/outputs/", "outputs/")
                if os.path.exists(old_image_path):
                    new_image_filename = os.path.basename(old_image_path).replace(f"{job_id}_", "")
                    new_image_path = os.path.join(story_dir, new_image_filename)
                    import shutil
                    shutil.copy2(old_image_path, new_image_path)
                    scene_data["image_url"] = f"/api/saved-stories/{story_id}/{new_image_filename}"
                    logger.info(f"Copied image: {old_image_path} -> {new_image_path}")
            
            # Copy audio file if it exists
            if s.get("audio_url") and s["audio_url"].startswith("/api/outputs/"):
                old_audio_path = s["audio_url"].replace("/api/outputs/", "outputs/")
                if os.path.exists(old_audio_path):
                    new_audio_filename = os.path.basename(old_audio_path).replace(f"{job_id}_", "")
                    new_audio_path = os.path.join(story_dir, new_audio_filename)
                    import shutil
                    shutil.copy2(old_audio_path, new_audio_path)
                    scene_data["audio_url"] = f"/api/saved-stories/{story_id}/{new_audio_filename}"
                    logger.info(f"Copied audio: {old_audio_path} -> {new_audio_path}")
            
            updated_scenes.append(scene_data)
        
        story_data = {
            "title": status["title"],
            "scenes": updated_scenes
        }
        
        success = StoryOperations.save_story(
            user_id=user['id'],
            story_id=story_id,
            name=story_name,
            story_data=story_data
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save story to the database.")
        
        logger.info(f"Story {story_id} saved successfully with {len(updated_scenes)} scenes")
        return {"story_id": story_id, "message": "Story saved successfully"}
    
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
    
    for scene in story_data.get("scenes", []):
        if scene.get("image_url"):
            scene["image_url"] = scene["image_url"].replace("/api/outputs/", f"/api/saved-stories/{story_id}/")
        if scene.get("audio_url"):
            scene["audio_url"] = scene["audio_url"].replace("/api/outputs/", f"/api/saved-stories/{story_id}/")
            
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
