import os
import uuid
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

# 2. GLOBAL JOBS STORE
jobs = {}

# 3. MIDDLEWARE & STATIC FILES
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves the generated MP3 and PNG files
app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

# 4. PARALLEL TASK HELPER
async def generate_scene_media(job_id: str, i: int, scene: dict):
    """Generates image and audio simultaneously for a single scene."""
    try:
        # We use asyncio.to_thread because the Gemini SDK is synchronous
        img_task = asyncio.to_thread(gemini.generate_image, scene["image_description"])
        aud_task = asyncio.to_thread(gemini.generate_voiceover, scene["text"])
        
        # Start both AI requests at once
        img_bytes, aud_bytes = await asyncio.gather(img_task, aud_task)

        # Save Image
        if img_bytes:
            img_name = f"{job_id}_scene_{i}.png"
            with open(os.path.join("outputs", img_name), "wb") as f:
                f.write(img_bytes)
            scene["image_url"] = f"/api/outputs/{img_name}"

        # Save Audio (Binary Safe)
        if aud_bytes:
            aud_name = f"{job_id}_scene_{i}.mp3"
            with open(os.path.join("outputs", aud_name), "wb") as f:
                f.write(aud_bytes)
            scene["audio_url"] = f"/api/outputs/{aud_name}"
            print(f"SUCCESS: Saved binary audio for Scene {i}")
            
    except Exception as e:
        print(f"Media Generation Error (Scene {i}): {e}")

# 5. BACKGROUND WORKFLOW
async def run_ai_workflow(job_id: str, file_path: str, grade_level: str):
    try:
        jobs[job_id]["progress"] = 10
        # Step 1: Text Generation (Must happen first)
        story_data = await asyncio.to_thread(gemini.process_file_to_story, file_path, grade_level)
        
        if not story_data or "scenes" not in story_data:
            raise Exception("Invalid AI response format.")

        scenes = story_data["scenes"]
        jobs[job_id]["progress"] = 30

        # Step 2: Parallel Media Generation for all scenes
        tasks = [generate_scene_media(job_id, i, scene) for i, scene in enumerate(scenes)]
        await asyncio.gather(*tasks)

        # Finalize
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = story_data

    except Exception as e:
        print(f"Workflow Failure: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

# 6. API ROUTES
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
    background_tasks.add_task(run_ai_workflow, job_id, upload_path, grade_level)
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/api/avatars")
async def get_avatars():
    return [
        {"id": "wizard", "name": "Professor Paws", "description": "Wise teacher."},
        {"id": "robot", "name": "Robo-Buddy", "description": "Tech expert."},
        {"id": "dinosaur", "name": "Dino-Explorer", "description": "Nature guide."}
    ]