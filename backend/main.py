import os
import uuid
import json
import asyncio
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from services.gemini_service import GeminiService

# Initialize FastAPI
app = FastAPI()
gemini = GeminiService()

# 1. ENSURE DIRECTORIES EXIST
# This creates the folders on the container startup if they don't exist
os.makedirs("outputs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# 2. CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. STATIC FILE SERVING
# This allows the frontend to access generated images/audio via URL
app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

# In-memory store for tracking jobs
jobs = {}

# 4. BACKGROUND WORKFLOW LOGIC
def run_ai_workflow(job_id: str, file_path: str):
    try:
        # Step 1: Analyze Document
        jobs[job_id]["progress"] = 10
        story_data = gemini.process_file_to_story(file_path)
        
        if not story_data or "scenes" not in story_data:
            raise Exception("AI failed to generate story structure.")

        # Step 2: Generate Media for each scene
        total_scenes = len(story_data["scenes"])
        for i, scene in enumerate(story_data["scenes"]):
            # Update progress (scales from 20% to 90%)
            progress_val = 20 + int((i / total_scenes) * 70)
            jobs[job_id]["progress"] = progress_val
            
            # Generate Image
            image_bytes = gemini.generate_image(scene["image_description"])
            if image_bytes:
                img_filename = f"{job_id}_scene_{i}.png"
                img_path = os.path.join("outputs", img_filename)
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                # This URL matches the app.mount path above
                scene["image_url"] = f"/api/outputs/{img_filename}"

            # Generate Audio
            audio_bytes = gemini.generate_voiceover(scene["text"])
            if audio_bytes:
                audio_filename = f"{job_id}_scene_{i}.mp3"
                audio_path = os.path.join("outputs", audio_filename)
                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)
                scene["audio_url"] = f"/api/outputs/{audio_filename}"

        # Final Step: Complete
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = story_data

    except Exception as e:
        print(f"Error in background job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

# 5. API ROUTES

@app.get("/api/avatars")
async def get_avatars():
    """Returns the list of characters for the AvatarSelector component"""
    return [
        {"id": "teacher", "name": "Professor Paws", "image": "https://img.icons8.com/bubbles/200/teacher.png"},
        {"id": "robot", "name": "Robo-Buddy", "image": "https://img.icons8.com/bubbles/200/robot-vacuum.png"},
        {"id": "explorer", "name": "Captain Quest", "image": "https://img.icons8.com/bubbles/200/trekking.png"}
    ]

@app.post("/api/upload")
async def upload_story(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Starts the background AI generation process"""
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_extension = os.path.splitext(file.filename)[1]
    saved_filename = f"{job_id}{file_extension}"
    upload_path = os.path.join("uploads", saved_filename)
    
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Initialize job status
    jobs[job_id] = {"status": "processing", "progress": 0, "result": None}
    
    # Start background task
    background_tasks.add_task(run_ai_workflow, job_id, upload_path)
    
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Endpoint for the frontend to poll progress"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

# Health check route
@app.get("/health")
async def health_check():
    return {"status": "healthy"}