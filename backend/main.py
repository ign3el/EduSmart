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

# 2. GLOBAL JOBS STORE (In-memory tracking)
jobs = {}

# 3. MIDDLEWARE & STATIC FILES
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Important for serving the generated images and audio
app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

# 4. AVATARS ENDPOINT (Placed first for routing priority)
@app.get("/api/avatars")
async def get_avatars():
    return [
        {"id": "wizard", "name": "Professor Paws", "description": "Wise teacher."},
        {"id": "robot", "name": "Robo-Buddy", "description": "Tech explorer."},
        {"id": "dinosaur", "name": "Dino-Explorer", "description": "Nature guide."}
    ]

# 5. BACKGROUND PROCESSING LOGIC
async def generate_scene_media(job_id: str, i: int, scene: dict):
    """Parallel generation for a single scene with staggered start."""
    # Gentle stagger to prevent 500 errors from Google TTS
    await asyncio.sleep(i * 1.5) 
    
    try:
        # Run image and audio generation simultaneously
        img_task = asyncio.to_thread(gemini.generate_image, scene["image_description"])
        aud_task = asyncio.to_thread(gemini.generate_voiceover, scene["text"])
        
        image_bytes, audio_bytes = await asyncio.gather(img_task, aud_task)

        if image_bytes:
            img_name = f"{job_id}_scene_{i}.png"
            with open(os.path.join("outputs", img_name), "wb") as f:
                f.write(image_bytes)
            scene["image_url"] = f"/api/outputs/{img_name}"

        if audio_bytes:
            aud_name = f"{job_id}_scene_{i}.mp3"
            with open(os.path.join("outputs", aud_name), "wb") as f:
                f.write(audio_bytes)
            scene["audio_url"] = f"/api/outputs/{aud_name}"
            print(f"DEBUG: Saved binary audio for Scene {i} ({len(audio_bytes)} bytes)")
            
    except Exception as e:
        print(f"DEBUG: Media Task Failure for Scene {i}: {e}")

async def run_ai_workflow(job_id: str, file_path: str, grade_level: str):
    """Main background workflow."""
    try:
        jobs[job_id]["progress"] = 10
        # Step 1: Generate Story Structure
        story_data = await asyncio.to_thread(gemini.process_file_to_story, file_path, grade_level)
        
        if not story_data or "scenes" not in story_data:
            raise Exception("AI failed to return valid story scenes.")

        jobs[job_id]["progress"] = 30
        
        # Step 2: Parallelize media generation across all scenes
        tasks = [generate_scene_media(job_id, i, scene) for i, scene in enumerate(story_data["scenes"])]
        await asyncio.gather(*tasks)

        # Finalize
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = story_data
        print(f"DEBUG: Workflow finished for job {job_id}")

    except Exception as e:
        print(f"CRITICAL WORKFLOW ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

# 6. API ROUTES (Upload & Status)
@app.post("/api/upload")
async def upload_story(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    grade_level: str = Form("Grade 4")
):
    job_id = str(uuid.uuid4())
    upload_path = os.path.join("uploads", f"{job_id}_{file.filename}")
    
    # Read and save the uploaded file
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)

    jobs[job_id] = {"status": "processing", "progress": 0, "result": None}
    
    # Offload the heavy AI work to a background task
    background_tasks.add_task(run_ai_workflow, job_id, upload_path, grade_level)
    
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]