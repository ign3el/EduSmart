import os
from dotenv import load_dotenv
import uuid
import asyncio
import mimetypes
import io
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
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

@app.get("/api/avatars")
async def get_avatars():
    return [
        {"id": "wizard", "name": "Professor Paws", "description": "Wise teacher."},
        {"id": "robot", "name": "Robo-Buddy", "description": "Tech explorer."},
        {"id": "dinosaur", "name": "Dino-Explorer", "description": "Nature guide."}
    ]

async def generate_scene_media(job_id: str, i: int, scene: dict, voice: str = "en-US-JennyNeural"):
    # Stagger requests by 5 seconds to stay under RPM limits
    await asyncio.sleep(i * 5.0) 
    
    try:
        img_task = asyncio.to_thread(gemini.generate_image, scene["image_description"])
        aud_task = asyncio.to_thread(gemini.generate_voiceover, scene["text"], voice)
        
        image_bytes, audio_bytes = await asyncio.gather(img_task, aud_task)

        if image_bytes:
            img_name = f"{job_id}_scene_{i}.png"
            with open(os.path.join("outputs", img_name), "wb") as f:
                f.write(image_bytes)
            scene["image_url"] = f"/api/outputs/{img_name}"

        if audio_bytes:
            aud_name = f"{job_id}_scene_{i}.mp3"  # Edge-TTS returns MP3 format
            aud_path = os.path.join("outputs", aud_name)
            
            with open(aud_path, "wb") as f:
                f.write(audio_bytes)
            
            file_size = os.path.getsize(aud_path)
            print(f"✓ Audio saved for scene {i}: {file_size} bytes (MP3)")
            
            scene["audio_url"] = f"/api/outputs/{aud_name}"
            
    except Exception as e:
        print(f"FAILED: Media for Scene {i}: {e}")

async def run_ai_workflow(job_id: str, file_path: str, grade_level: str, voice: str = "en-US-JennyNeural"):
    try:
        jobs[job_id]["progress"] = 10
        story_data = await asyncio.to_thread(gemini.process_file_to_story, file_path, grade_level)
        
        if not story_data:
            raise Exception("AI failed to generate story content.")

        jobs[job_id]["progress"] = 30
        tasks = [generate_scene_media(job_id, i, scene, voice) for i, scene in enumerate(story_data["scenes"])]
        await asyncio.gather(*tasks)

        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
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
    
    jobs[job_id] = {"status": "processing", "progress": 0, "result": None}
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
        story_dir = os.path.join("saved_stories", story_id)
        os.makedirs(story_dir, exist_ok=True)
        
        # Save metadata and story content
        metadata = {
            "id": story_id,
            "name": story_name,
            "job_id": job_id,
            "saved_at": str(uuid.uuid1().time),
            "story_data": story_data
        }
        
        import json
        with open(os.path.join(story_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Copy all output files for this job to saved_stories
        for filename in os.listdir("outputs"):
            if filename.startswith(job_id):
                src = os.path.join("outputs", filename)
                dst = os.path.join(story_dir, filename)
                import shutil
                shutil.copy2(src, dst)
        
        return {"story_id": story_id, "message": "Story saved successfully"}
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
        
        return {
            "name": metadata["name"],
            "story_data": story_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load story: {str(e)}")

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
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add metadata
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # Add all media files
            for filename in os.listdir(story_dir):
                if filename != "metadata.json":
                    file_path = os.path.join(story_dir, filename)
                    zip_file.write(file_path, filename)
        
        zip_buffer.seek(0)
        story_name = metadata["name"].replace(" ", "_").replace("/", "_")
        filename = f"{story_name}_{story_id[:8]}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
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