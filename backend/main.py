import os
import uuid
import json
import asyncio
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from services.gemini_service import GeminiService

app = FastAPI()
gemini = GeminiService()

# 1. ENSURE DIRECTORIES EXIST
os.makedirs("outputs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# 2. CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. STATIC FILE SERVING (Fixes 404 Errors)
app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

# In-memory store for tracking jobs
jobs = {}

# 4. DYNAMIC BACKGROUND WORKFLOW
def run_ai_workflow(job_id: str, file_path: str):
    try:
        # Step 1: Analyze Document & Generate Story Structure
        jobs[job_id]["progress"] = 10
        story_data = gemini.process_file_to_story(file_path)
        
        if not story_data or "scenes" not in story_data:
            raise Exception("AI failed to generate a dynamic story structure.")

        # Step 2: Generate Media for every scene dynamically
        scenes = story_data["scenes"]
        total_scenes = len(scenes)
        
        for i, scene in enumerate(scenes):
            # Update progress based on the dynamic number of scenes
            progress_val = 15 + int((i / total_scenes) * 80)
            jobs[job_id]["progress"] = progress_val
            
            # Generate Image
            image_bytes = gemini.generate_image(scene["image_description"])
            if image_bytes:
                img_filename = f"{job_id}_scene_{i}.png"
                with open(os.path.join("outputs", img_filename), "wb") as f:
                    f.write(image_bytes)
                scene["image_url"] = f"/api/outputs/{img_filename}"

            # Generate Audio (Narration)
            audio_bytes = gemini.generate_voiceover(scene["text"])
            if audio_bytes:
                audio_filename = f"{job_id}_scene_{i}.mp3"
                with open(os.path.join("outputs", audio_filename), "wb") as f:
                    f.write(audio_bytes)
                scene["audio_url"] = f"/api/outputs/{audio_filename}"

        # Final Step: Job Complete
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
    return [
        {"id": "teacher", "name": "Professor Paws", "image": "https://img.icons8.com/bubbles/200/teacher.png"},
        {"id": "robot", "name": "Robo-Buddy", "image": "https://img.icons8.com/bubbles/200/robot-vacuum.png"},
        {"id": "explorer", "name": "Captain Quest", "image": "https://img.icons8.com/bubbles/200/trekking.png"}
    ]

@app.post("/api/upload")
async def upload_story(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    upload_path = os.path.join("uploads", f"{job_id}{file_ext}")
    
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)

    jobs[job_id] = {"status": "processing", "progress": 0, "result": None}
    background_tasks.add_task(run_ai_workflow, job_id, upload_path)
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]