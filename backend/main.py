import os, uuid, json, asyncio
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.gemini_service import GeminiService

app = FastAPI()
gemini = GeminiService()

# Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for tracking jobs
# Format: { "job_id": { "status": "processing", "progress": 0, "result": None } }
jobs = {}

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
            # Update progress based on scene count
            # Progress goes from 20% to 90% during scene generation
            progress_val = 20 + int((i / total_scenes) * 70)
            jobs[job_id]["progress"] = progress_val
            
            # Generate Image
            image_bytes = gemini.generate_image(scene["image_description"])
            if image_bytes:
                img_path = f"outputs/{job_id}_scene_{i}.png"
                with open(img_path, "wb") as f: f.write(image_bytes)
                scene["image_url"] = f"/api/outputs/{job_id}_scene_{i}.png"

            # Generate Audio
            audio_bytes = gemini.generate_voiceover(scene["text"])
            if audio_bytes:
                audio_path = f"outputs/{job_id}_scene_{i}.mp3"
                with open(audio_path, "wb") as f: f.write(audio_bytes)
                scene["audio_url"] = f"/api/outputs/{job_id}_scene_{i}.mp3"

        # Final Step: Complete
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = story_data

    except Exception as e:
        print(f"Error in background job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.post("/api/upload")
async def upload_story(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_path = f"uploads/{file.filename}"
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
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]