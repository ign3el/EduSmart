import os
import uuid
import json
import asyncio
import base64
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from services.gemini_service import GeminiService

app = FastAPI()
gemini = GeminiService()

# 1. SETUP DIRECTORIES
os.makedirs("outputs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# 2. INITIALIZE GLOBAL JOBS STORE
jobs = {}

# 3. MIDDLEWARE & STATIC FILES
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves the static assets with correct MIME types handled by FastAPI
app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

# 4. PARALLEL MEDIA GENERATION HELPER
async def generate_scene_media(job_id: str, i: int, scene: dict):
    """
    Generates both image and audio for a specific scene simultaneously.
    Uses asyncio.to_thread to prevent blocking the event loop with synchronous SDK calls.
    """
    try:
        # Run Image and Audio AI calls in parallel
        image_task = asyncio.to_thread(gemini.generate_image, scene["image_description"])
        audio_task = asyncio.to_thread(gemini.generate_voiceover, scene["text"])
        
        image_bytes, audio_data = await asyncio.gather(image_task, audio_task)

        # 1. Save Image
        if image_bytes:
            img_name = f"{job_id}_scene_{i}.png"
            with open(os.path.join("outputs", img_name), "wb") as f:
                f.write(image_bytes)
            scene["image_url"] = f"/api/outputs/{img_name}"

        # 2. Save Audio with Binary Fix
        if audio_data:
            aud_name = f"{job_id}_scene_{i}.mp3"
            full_path = os.path.join("outputs", aud_name)
            
            with open(full_path, "wb") as f:
                # Critical: Decode if the SDK returned a base64 string, 
                # otherwise write the raw bytes directly.
                if isinstance(audio_data, str):
                    try:
                        f.write(base64.b64decode(audio_data))
                    except Exception:
                        # Fallback if string is somehow not base64
                        f.write(audio_data.encode('utf-8'))
                else:
                    f.write(audio_data)
            
            scene["audio_url"] = f"/api/outputs/{aud_name}"
            print(f"DEBUG: Scene {i} audio saved: {os.path.getsize(full_path)} bytes")
            
    except Exception as e:
        print(f"ERROR generating media for scene {i}: {e}")

# 5. BACKGROUND WORKFLOW
async def run_ai_workflow(job_id: str, file_path: str, grade_level: str):
    try:
        # Step 1: Story & Quiz Generation (First, to get the scene text)
        jobs[job_id]["progress"] = 10
        print(f"DEBUG: Analyzing PDF for {grade_level}...")
        
        story_data = await asyncio.to_thread(gemini.process_file_to_story, file_path, grade_level)
        
        if not story_data or "scenes" not in story_data:
            raise Exception("AI failed to extract story scenes.")

        scenes = story_data["scenes"]
        jobs[job_id]["progress"] = 30
        print(f"DEBUG: Story created with {len(scenes)} scenes. Starting parallel media generation...")

        # Step 2: Parallel Processing
        # Create a list of tasks for every scene to run at the SAME TIME
        tasks = [generate_scene_media(job_id, i, scene) for i, scene in enumerate(scenes)]
        await asyncio.gather(*tasks)

        # Finalize
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = story_data
        print(f"DEBUG: Job {job_id} fully completed.")

    except Exception as e:
        print(f"WORKFLOW ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

# 6. API ROUTES
@app.get("/api/avatars")
async def get_avatars():
    return [
        {"id": "wizard", "name": "Professor Paws", "description": "A wise teacher guide."},
        {"id": "robot", "name": "Robo-Buddy", "description": "Explains with high-tech sensors."},
        {"id": "dinosaur", "name": "Dino-Explorer", "description": "Explores nature and history."}
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

    jobs[job_id] = {"status": "processing", "progress": 0, "result": None}
    
    # We use await run_ai_workflow if we want it to be fully async
    background_tasks.add_task(run_ai_workflow, job_id, upload_path, grade_level)
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]