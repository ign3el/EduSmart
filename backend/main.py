import os
from dotenv import load_dotenv
import uuid
import asyncio
import time
import mimetypes
import io
import re
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from services.gemini_service import GeminiService
from models import StoryResponse

# Fix for NotSupportedError in browsers
load_dotenv()  # current working directory
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))
mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('image/png', '.png')

app = FastAPI()
gemini = GeminiService()

@app.on_event("startup")
async def start_cleanup_task():
    asyncio.create_task(cleanup_scheduler())

os.makedirs("outputs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("saved_stories", exist_ok=True)
jobs = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

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

# -------- Periodic cleanup for temp files --------
CLEAN_PATHS = ["outputs", "uploads"]
CLEAN_AGE_SECONDS = 60 * 60  # 1 hour
CLEAN_INTERVAL_SECONDS = 60 * 60 * 24  # 24 hours

async def cleanup_old_files():
    now = time.time()
    removed = 0
    for path in CLEAN_PATHS:
        if not os.path.exists(path):
            continue
        for fname in os.listdir(path):
            fpath = os.path.join(path, fname)
            try:
                mtime = os.path.getmtime(fpath)
                if now - mtime > CLEAN_AGE_SECONDS:
                    os.remove(fpath)
                    removed += 1
            except Exception:
                continue
    if removed:
        print(f"Cleanup removed {removed} stale files from outputs/uploads")

async def cleanup_scheduler():
    while True:
        # Sleep until next local midnight to avoid drift from simple intervals
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_seconds = max(0, (next_midnight - now).total_seconds())
        await asyncio.sleep(sleep_seconds)

        try:
            await cleanup_old_files()
        except Exception as e:
            print(f"Cleanup scheduler error: {e}")

@app.get("/api/avatars")
async def get_avatars():
    return [
        {"id": "wizard", "name": "Professor Paws", "description": "Wise teacher."},
        {"id": "robot", "name": "Robo-Buddy", "description": "Tech explorer."},
        {"id": "dinosaur", "name": "Dino-Explorer", "description": "Nature guide."}
    ]

async def generate_scene_media(job_id: str, i: int, scene: dict, voice: str = "en-US-JennyNeural", story_seed: Optional[int] = None):
    """Generate image and audio for a scene with retry logic for audio. Uses story_seed for character consistency."""
    try:
        # No per-scene stagger - all scenes in batch run in parallel
        # Parallel image + audio generation with story seed for consistent characters
        img_task = asyncio.to_thread(gemini.generate_image, scene["image_description"], scene.get("text", ""), story_seed)
        aud_task = asyncio.to_thread(gemini.generate_voiceover, scene["text"], voice)
        
        image_bytes, audio_bytes = await asyncio.gather(img_task, aud_task, return_exceptions=False)

        if image_bytes:
            img_name = f"{job_id}_scene_{i}.png"
            with open(os.path.join("outputs", img_name), "wb") as f:
                f.write(image_bytes)
            scene["image_url"] = f"/api/outputs/{img_name}"

        # Retry audio generation if failed (Edge-TTS can be flaky)
        if not audio_bytes:
            print(f"⚠ Audio retry for scene {i}...")
            await asyncio.sleep(2)
            audio_bytes = await asyncio.to_thread(gemini.generate_voiceover, scene["text"], voice)
        
        if audio_bytes:
            aud_name = f"{job_id}_scene_{i}.mp3"
            aud_path = os.path.join("outputs", aud_name)
            
            with open(aud_path, "wb") as f:
                f.write(audio_bytes)
            
            file_size = os.path.getsize(aud_path)
            print(f"✓ Scene {i}: {file_size} bytes audio")
            
            scene["audio_url"] = f"/api/outputs/{aud_name}"
        else:
            print(f"⚠ Scene {i}: Audio generation failed (continuing with placeholder)")
            
    except Exception as e:
        print(f"FAILED: Media for Scene {i}: {e}")

async def run_ai_workflow(job_id: str, file_path: str, grade_level: str, voice: str = "en-US-JennyNeural"):
    try:
        jobs[job_id]["progress"] = 10
        story_data = await asyncio.to_thread(gemini.process_file_to_story, file_path, grade_level)
        
        if not story_data:
            raise Exception("AI failed to generate story content.")

        jobs[job_id]["progress"] = 30

        # Generate a unique seed for this story to keep characters consistent across all scenes
        import hashlib
        story_seed = int(hashlib.md5(job_id.encode()).hexdigest()[:8], 16) % 2147483647

        scenes = story_data.get("scenes", [])
        total_scenes = len(scenes) if scenes else 1

        # Process scenes in aggressive parallel batches of 5 (max safe concurrency)
        batch_size = 5
        for batch_start in range(0, total_scenes, batch_size):
            # Small delay between batches to prevent API throttling
            if batch_start > 0:
                await asyncio.sleep(0.5)
            
            batch_end = min(batch_start + batch_size, total_scenes)
            batch = [
                generate_scene_media(job_id, i, scenes[i], voice, story_seed)
                for i in range(batch_start, batch_end)
            ]
            
            # Wait for entire batch to complete (all 5 scenes in parallel)
            await asyncio.gather(*batch)
            
            # Update progress
            scene_progress = 30 + int(((batch_end) / total_scenes) * 65)
            jobs[job_id]["progress"] = scene_progress
            print(f"✓ Batch {batch_start // batch_size + 1} complete: {batch_end}/{total_scenes} scenes (story_seed={story_seed})")

        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        story_data["upload_url"] = f"/api/uploads/{os.path.basename(file_path)}"
        jobs[job_id]["result"] = story_data
    except Exception as e:
        print(f"WORKFLOW ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.post("/api/upload")
async def upload_story(background_tasks: BackgroundTasks, file: UploadFile = File(...), grade_level: str = Form("Grade 4"), voice: str = Form("en-US-JennyNeural")):
    job_id = str(uuid.uuid4())
    upload_path = os.path.join("uploads", f"{job_id}_{file.filename}")
    with open(upload_path, "wb") as f:
        f.write(await file.read())
    
    jobs[job_id] = {"status": "processing", "progress": 0, "result": None, "upload_path": upload_path}
    background_tasks.add_task(run_ai_workflow, job_id, upload_path, grade_level, voice)
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.post("/api/save-story/{job_id}")
async def save_story(job_id: str, story_name: str = Form(...)):
    """Save a completed story with a custom name."""
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="Story not found or not completed")
    
    try:
        story_data = jobs[job_id]["result"]
        story_id = str(uuid.uuid4())
        folder_name = _safe_story_dirname(story_name, story_id)
        story_dir = os.path.join("saved_stories", folder_name)
        os.makedirs(story_dir, exist_ok=True)

        # Persist the originally uploaded file alongside the story and remove from uploads
        upload_path = jobs[job_id].get("upload_path")
        upload_filename = None
        if upload_path and os.path.exists(upload_path):
            upload_filename = os.path.basename(upload_path)
            if upload_filename.startswith(f"{job_id}_"):
                upload_filename = upload_filename[len(job_id) + 1 :]
            import shutil
            try:
                shutil.move(upload_path, os.path.join(story_dir, upload_filename))
            except Exception:
                # Fallback to copy-then-remove if move fails across devices
                shutil.copy2(upload_path, os.path.join(story_dir, upload_filename))
                os.remove(upload_path)
            story_data["upload_url"] = f"/api/saved-stories/{folder_name}/{upload_filename}"
        
        # Save metadata and story content
        metadata = {
            "id": folder_name,
            "name": story_name,
            "job_id": job_id,
            "saved_at": str(uuid.uuid1().time),
            "story_data": story_data
        }
        
        import json
        with open(os.path.join(story_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Move all output files for this job to saved_stories, removing them from outputs
        for filename in os.listdir("outputs"):
            if filename.startswith(job_id):
                src = os.path.join("outputs", filename)
                dst = os.path.join(story_dir, filename)
                import shutil
                try:
                    shutil.move(src, dst)
                except Exception:
                    shutil.copy2(src, dst)
                    os.remove(src)
        
        return {"story_id": folder_name, "message": "Story saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save story: {str(e)}")

@app.get("/api/list-stories")
async def list_stories():
    """List all saved stories."""
    stories = []
    try:
        for story_id in os.listdir("saved_stories"):
            metadata_path = os.path.join("saved_stories", story_id, "metadata.json")
            if os.path.exists(metadata_path):
                import json
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    stories.append({
                        "id": metadata["id"],
                        "name": metadata["name"],
                        "saved_at": metadata["saved_at"]
                    })
        return sorted(stories, key=lambda x: x["saved_at"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list stories: {str(e)}")

@app.get("/api/load-story/{story_id}")
async def load_story(story_id: str):
    """Load a saved story."""
    story_dir = os.path.join("saved_stories", story_id)
    metadata_path = os.path.join(story_dir, "metadata.json")
    
    if not os.path.exists(metadata_path):
        raise HTTPException(status_code=404, detail="Story not found")
    
    try:
        import json
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        # Update URLs to point to saved_stories
        story_data = metadata["story_data"]
        for scene in story_data.get("scenes", []):
            if scene.get("image_url"):
                filename = os.path.basename(scene["image_url"])
                scene["image_url"] = f"/api/saved-stories/{story_id}/{filename}"
            if scene.get("audio_url"):
                filename = os.path.basename(scene["audio_url"])
                scene["audio_url"] = f"/api/saved-stories/{story_id}/{filename}"

        if story_data.get("upload_url"):
            upload_filename = os.path.basename(story_data["upload_url"])
            story_data["upload_url"] = f"/api/saved-stories/{story_id}/{upload_filename}"
        
        return {
            "name": metadata["name"],
            "story_data": story_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load story: {str(e)}")

@app.delete("/api/delete-story/{story_id}")
async def delete_story(story_id: str):
    """Delete a saved story."""
    story_dir = os.path.join("saved_stories", story_id)
    metadata_path = os.path.join(story_dir, "metadata.json")
    
    if not os.path.exists(metadata_path):
        raise HTTPException(status_code=404, detail="Story not found")
    
    try:
        import shutil
        shutil.rmtree(story_dir)
        return {"message": "Story deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete story: {str(e)}")


@app.delete("/api/cleanup/{job_id}")
async def cleanup_job(job_id: str):
    """Delete all files associated with an unsaved job."""
    try:
        # Delete uploaded file
        for filename in os.listdir("uploads"):
            if filename.startswith(job_id):
                os.remove(os.path.join("uploads", filename))
        
        # Delete output files
        for filename in os.listdir("outputs"):
            if filename.startswith(job_id):
                os.remove(os.path.join("outputs", filename))
        
        # Remove job from memory
        if job_id in jobs:
            del jobs[job_id]
        
        return {"message": "Cleanup successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@app.get("/api/export-story/{story_id}")
async def export_story(story_id: str):
    """Export a saved story as a downloadable ZIP file."""
    story_dir = os.path.join("saved_stories", story_id)
    metadata_path = os.path.join(story_dir, "metadata.json")
    
    if not os.path.exists(metadata_path):
        raise HTTPException(status_code=404, detail="Story not found")
    
    try:
        import json
        import zipfile
        import io
        
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        # Create ZIP file in memory (buffered approach)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add metadata
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # Add all media files
            for filename in os.listdir(story_dir):
                if filename != "metadata.json":
                    file_path = os.path.join(story_dir, filename)
                    # Only add files, skip directories
                    if os.path.isfile(file_path):
                        zip_file.write(file_path, arcname=filename)
        
        zip_buffer.seek(0)
        story_name = metadata["name"].replace(" ", "_").replace("/", "_")
        filename = f"{story_name}_{story_id[:8]}.zip"
        
        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/export-job/{job_id}")
async def export_job(job_id: str):
    """Export a newly generated story (unsaved) as a downloadable ZIP file."""
    try:
        import json
        import zipfile
        
        # Check if job exists and is completed
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        if job["status"] != "completed" or not job.get("result"):
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        result = job["result"]
        story_title = result.get("title", "Story").replace(" ", "_").replace("/", "_")
        filename = f"{story_title}_{job_id[:8]}.zip"
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add story metadata/data as JSON
            zip_file.writestr("story_data.json", json.dumps(result, indent=2))
            
            # Add all generated media files from outputs folder
            outputs_dir = "outputs"
            if os.path.exists(outputs_dir):
                for filename_in_outputs in os.listdir(outputs_dir):
                    if filename_in_outputs.startswith(job_id):
                        file_path = os.path.join(outputs_dir, filename_in_outputs)
                        if os.path.isfile(file_path):
                            # Add with basename only (relative to outputs)
                            arcname = os.path.basename(file_path).replace(f"{job_id}_", "")
                            zip_file.write(file_path, arcname=arcname)
        
        zip_buffer.seek(0)
        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/api/import-story")
async def import_story(file: UploadFile = File(...)):
    """Import a story from a ZIP file."""
    try:
        import zipfile
        import json
        import uuid
        
        # Read ZIP file
        zip_content = await file.read()
        zip_buffer = io.BytesIO(zip_content)
        
        story_id = str(uuid.uuid4())
        story_dir = os.path.join("saved_stories", story_id)
        os.makedirs(story_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            # Extract all files
            zip_file.extractall(story_dir)
            
            # Validate metadata
            metadata_path = os.path.join(story_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                raise ValueError("Invalid story package: missing metadata.json")
            
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            # Update story ID in metadata
            metadata["id"] = story_id
            metadata["saved_at"] = str(uuid.uuid1().time)
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
        
        return {
            "story_id": story_id,
            "name": metadata["name"],
            "message": "Story imported successfully"
        }
    except Exception as e:
        # Cleanup on failure
        if os.path.exists(story_dir):
            import shutil
            shutil.rmtree(story_dir)
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")