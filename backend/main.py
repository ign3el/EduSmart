import os
import uuid
import json
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from services.gemini_service import GeminiService

app = FastAPI()
gemini = GeminiService()

# 1. SETUP DIRECTORIES
os.makedirs("outputs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# 2. INITIALIZE GLOBAL JOBS STORE (Fixes your Pylance error)
jobs = {}

# 3. MIDDLEWARE & STATIC FILES
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

# 4. BACKGROUND WORKFLOW
def run_ai_workflow(job_id: str, file_path: str, grade_level: str):
    try:
        # Step 1: Story & Quiz Generation
        jobs[job_id]["progress"] = 10
        story_data = gemini.process_file_to_story(file_path, grade_level)
        
        if not story_data or "scenes" not in story_data:
            raise Exception("AI failed to extract content. Please check the file format.")

        scenes = story_data["scenes"]
        total_scenes = len(scenes)

        # Step 2: Media Generation for each dynamic scene
        for i, scene in enumerate(scenes):
            # Dynamic progress tracking
            progress_val = 15 + int((i / total_scenes) * 80)
            jobs[job_id]["progress"] = progress_val
            
            # Generate Image (Gemini 3)
            image_bytes = gemini.generate_image(scene["image_description"])
            if image_bytes:
                img_name = f"{job_id}_scene_{i}.png"
                with open(os.path.join("outputs", img_name), "wb") as f:
                    f.write(image_bytes)
                scene["image_url"] = f"/api/outputs/{img_name}"

            # Generate Audio (Gemini 2.5 TTS)
            audio_bytes = gemini.generate_voiceover(scene["text"])
            if audio_bytes:
                aud_name = f"{job_id}_scene_{i}.mp3"
                full_path = os.path.join("outputs", aud_name)
                with open(full_path, "wb") as f:
                    f.write(audio_bytes)
                # This URL must match your app.mount path
                scene["audio_url"] = f"/api/outputs/{aud_name}"
                print(f"DEBUG: Audio saved to {full_path}")

        # Finalize
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = story_data

    except Exception as e:
        print(f"WORKFLOW ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

# 5. API ROUTES
# In main.py, update this specific route:

@app.get("/api/avatars")
async def get_avatars():
    return [
        {
            "id": "wizard", 
            "name": "Professor Paws", 
            "description": "A wise teacher who knows all about the UAE desert!"
        },
        {
            "id": "robot", 
            "name": "Robo-Buddy", 
            "description": "Uses high-tech sensors to explain how plants survive."
        },
        {
            "id": "dinosaur", 
            "name": "Dino-Explorer", 
            "description": "Let's explore nature from the past to the present!"
        }
    ]

@app.post("/api/upload")
async def upload_story(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    grade_level: str = Form("Grade 4")
):
    job_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    upload_path = os.path.join("uploads", f"{job_id}{file_ext}")
    
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    # Initialize job entry
    jobs[job_id] = {"status": "processing", "progress": 0, "result": None}
    
    background_tasks.add_task(run_ai_workflow, job_id, upload_path, grade_level)
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]