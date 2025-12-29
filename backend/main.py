import os
import uuid
import asyncio
import mimetypes 
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from services.gemini_service import GeminiService
from models import StoryResponse

# CRITICAL: Fixes 'NotSupportedError' by sending correct headers
#
mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('image/png', '.png')

app = FastAPI()
gemini = GeminiService()

os.makedirs("outputs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
jobs = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.mount("/api/outputs", StaticFiles(directory="outputs"), name="outputs")

@app.get("/api/avatars")
async def get_avatars():
    return [
        {"id": "wizard", "name": "Professor Paws", "description": "Wise teacher."},
        {"id": "robot", "name": "Robo-Buddy", "description": "Tech explorer."},
        {"id": "dinosaur", "name": "Dino-Explorer", "description": "Nature guide."}
    ]

async def generate_scene_media(job_id: str, i: int, scene: dict):
    # Staggered requests to prevent 429 quota errors
    await asyncio.sleep(i * 4.0) 
    
    try:
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
            # Write as binary ('wb') to save the decoded MP3 bytes
            with open(os.path.join("outputs", aud_name), "wb") as f:
                f.write(audio_bytes)
            scene["audio_url"] = f"/api/outputs/{aud_name}"
            print(f"SUCCESS: Saved binary audio for scene {i}")
            
    except Exception as e:
        print(f"FAILED: Media for Scene {i}: {e}")

async def run_ai_workflow(job_id: str, file_path: str, grade_level: str):
    try:
        jobs[job_id]["progress"] = 10
        story_data = await asyncio.to_thread(gemini.process_file_to_story, file_path, grade_level)
        
        if not story_data:
            raise Exception("AI failed to generate story text.")

        jobs[job_id]["progress"] = 30
        tasks = [generate_scene_media(job_id, i, scene) for i, scene in enumerate(story_data["scenes"])]
        await asyncio.gather(*tasks)

        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = story_data
    except Exception as e:
        print(f"WORKFLOW ERROR: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.post("/api/upload")
async def upload_story(background_tasks: BackgroundTasks, file: UploadFile = File(...), grade_level: str = Form("Grade 4")):
    job_id = str(uuid.uuid4())
    upload_path = os.path.join("uploads", f"{job_id}_{file.filename}")
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
