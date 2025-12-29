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

# Standard static file mounting for FastAPI
app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

# 4. PARALLEL MEDIA GENERATION HELPER
async def generate_scene_media(job_id: str, i: int, scene: dict):
    """
    Generates image and audio for a scene simultaneously.
    Uses asyncio.to_thread to keep the Gemini SDK from blocking.
    """
    try:
        # Run AI requests for Image and Audio at the same time
        image_task = asyncio.to_thread(gemini.generate_image, scene["image_description"])
        audio_task = asyncio.to_thread(gemini.generate_voiceover, scene["text"])
        
        image_bytes, audio_data = await asyncio.gather(image_task, audio_task)

        # Save Image if generated
        if image_bytes:
            img_name = f"{job_id}_scene_{i}.png"
            with open(os.path.join("outputs", img_name), "wb") as f:
                f.write(image_bytes)
            scene["image_url"] = f"/api/outputs/{img_name}"

        # Save Audio with Binary Corruption Fix
        if audio_data:
            aud_name = f"{job_id}_scene_{i}.mp3"
            full_path = os.path.join("outputs", aud_name)
            
            with open(full_path, "wb") as f:
                # If the AI response is a string, it's Base64 and needs decoding.
                # If it's already bytes, write it directly.
                if isinstance(audio_data, str):
                    f.write(base64.b64decode(audio_data))
                else:
                    f.write(audio_data)
            
            scene["audio_url"] = f"/api/outputs/{aud_name}"
            print(f"DEBUG: Scene {i} audio saved: {os.path.getsize(full_path)} bytes")
            
    except Exception as e:
        print(f"ERROR in media generation for scene {i}: {e}")

# 5. BACKGROUND WORKFLOW
async def run_ai_workflow(job_id: str, file_path: str, grade_level: str):
    try:
        # Step 1: Analyze PDF & Create Story (Synchronous to get text first)
        jobs[job_id]["progress"] = 10
        story_data = await asyncio.to_thread(gemini.process_file_to_story, file_path, grade_level)
        
        if not story_data or "scenes" not in story_data:
            raise Exception("AI failed to create story scenes.")

        scenes = story_data["scenes"]
        jobs[job_id]["progress"] = 30

        # Step 2: Generate all Media in Parallel (Speed Improvement)
        # This starts tasks for ALL scenes at once
        media_tasks = [generate_scene_media(job_id, i, scene) for i, scene in enumerate(scenes)]
        await asyncio.gather(*media_tasks)

        # Finalize
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = story_data

    except Exception as e:
        print(f"WORKFLOW ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

# 6. API ROUTES
@app.get("/api/avatars")
async def get_avatars():
    return [
        {"id": "wizard", "name": "Professor Paws", "description": "Expert teacher guide."},
        {"id": "robot", "name": "Robo-Buddy", "description": "Explains with cool sensors."},
        {"id": "dinosaur", "name": "Dino-Explorer", "description": "Digs into history and nature."}
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
    background_tasks.add_task(run_ai_workflow, job_id, upload_path, grade_level)
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]