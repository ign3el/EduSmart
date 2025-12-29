from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os, uuid, json, random
from services.gemini_service import GeminiService

app = FastAPI()

# FIX: Ensure CORS matches your VPS domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

gemini = GeminiService()

# VPS Paths - Absolute for Docker
OUTPUT_DIR = "/app/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/api/avatars")
async def get_avatars():
    return {"avatars": [
        {"id": "beep", "name": "Beep", "url": "https://api.dicebear.com/7.x/bottts/svg?seed=beep"},
        {"id": "boop", "name": "Boop", "url": "https://api.dicebear.com/7.x/bottts/svg?seed=boop"}
    ]}

@app.post("/api/upload")
async def upload_story(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    # Process the story
    story_data = gemini.process_file_to_story(file.filename)

    if story_data is None:
        # This will tell the frontend EXACTLY what happened
        raise HTTPException(status_code=500, detail="Gemini API Model Not Found. Check backend logs.")
    
    if not story_data or "scenes" not in story_data:
        raise HTTPException(status_code=500, detail="Invalid Story Structure")

    for i, scene in enumerate(story_data["scenes"]):
        # Image Gen
        img_bytes = gemini.generate_image(scene.get("image_description", "scene"))
        if img_bytes:
            img_name = f"{session_id}_{i}.png"
            with open(os.path.join(OUTPUT_DIR, img_name), "wb") as f:
                f.write(img_bytes)
            scene["image_url"] = f"/outputs/{img_name}"

        # Audio Gen
        audio_bytes = gemini.generate_voiceover(scene.get("text", "Hello"))
        aud_name = f"{session_id}_{i}.wav"
        with open(os.path.join(OUTPUT_DIR, aud_name), "wb") as f:
            f.write(audio_bytes)
        scene["audio_url"] = f"/outputs/{aud_name}"

    result = {
        "story_id": session_id,
        "title": story_data.get("title", "New Story"),
        "scenes": story_data.get("scenes", [])
    }
    return result