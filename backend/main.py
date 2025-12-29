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
# Ensure these exist so open() calls don't fail
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

# Serves the mp3 and png files to the frontend
app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

# 4. BACKGROUND WORKFLOW
def run_ai_workflow(job_id: str, file_path: str, grade_level: str):
    try:
        # Step 1: Story & Quiz Generation
        print(f"STARTING WORKFLOW: Job {job_id} for {grade_level}")
        jobs[job_id]["progress"] = 10
        
        story_data = gemini.process_file_to_story(file_path, grade_level)
        
        if not story_data or "scenes" not in story_data:
            raise Exception("AI failed to extract content. Please check the file format or API quota.")

        scenes = story_data["scenes"]
        total_scenes = len(scenes)
        print(f"STORY GENERATED: {total_scenes} scenes found.")

        # Step 2: Media Generation for each dynamic scene
        for i, scene in enumerate(scenes):
            # Update progress based on scene completion
            progress_val = 15 + int((i / total_scenes) * 80)
            jobs[job_id]["progress"] = progress_val
            
            # --- IMAGE GENERATION ---
            print(f"GENERATING IMAGE: Scene {i}...")
            image_bytes = gemini.generate_image(scene["image_description"])
            if image_bytes:
                img_name = f"{job_id}_scene_{i}.png"
                img_path = os.path.join("outputs", img_name)
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                scene["image_url"] = f"/api/outputs/{img_name}"

            # --- AUDIO GENERATION (With Corruption Fix) ---
            print(f"GENERATING AUDIO: Scene {i}...")
            audio_data = gemini.generate_voiceover(scene["text"])
            
            if audio_data:
                aud_name = f"{job_id}_scene_{i}.mp3"
                full_path = os.path.join("outputs", aud_name)
                
                # FIX: Handle both Base64 strings and raw bytes to prevent corruption
                with open(full_path, "wb") as f:
                    if isinstance(audio_data, str):
                        # If AI returned a base64 string, decode it to binary
                        f.write(base64.b64decode(audio_data))
                    else:
                        # If AI returned raw bytes, write directly
                        f.write(audio_data)
                
                scene["audio_url"] = f"/api/outputs/{aud_name}"
                print(f"DEBUG: Audio saved successfully to {full_path} ({os.path.getsize(full_path)} bytes)")
            else:
                print(f"WARNING: No audio generated for scene {i}")

        # Finalize Job
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = story_data
        print(f"WORKFLOW COMPLETE: Job {job_id}")

    except Exception as e:
        print(f"WORKFLOW ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

# 5. API ROUTES
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
    
    # Save the uploaded PDF
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    # Initialize job entry in memory
    jobs[job_id] = {"status": "processing", "progress": 0, "result": None}
    
    # Start the AI heavy lifting in the background
    background_tasks.add_task(run_ai_workflow, job_id, upload_path, grade_level)
    
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]