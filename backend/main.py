from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from services.gemini_service import GeminiService
import os
import json
import uuid
import random
app = FastAPI()

app.add_middleware( CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], )

os.makedirs("uploads", exist_ok=True) 
os.makedirs("outputs", exist_ok=True) 
os.makedirs("saved_stories", exist_ok=True)

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

gemini = GeminiService()

# --- NEW: Mock Avatars Endpoint ---
@app.get("/api/avatars") 
async def get_avatars(): 
    """Returns dummy avatars to prevent Frontend 404 errors.""" 
    return [ 
        {"id": "beep", "name": "Beep", "url": "https://api.dicebear.com/7.x/bottts/svg?seed=beep"}, 
        {"id": "boop", "name": "Boop", "url": "https://api.dicebear.com/7.x/bottts/svg?seed=boop"}, 
        {"id": "zoom", "name": "Zoom", "url": "https://api.dicebear.com/7.x/bottts/svg?seed=zoom"} 
    ]

# --- MODIFIED: Accepts BOTH /api/upload AND /api/generate ---
@app.post("/api/generate") 
@app.post("/api/upload") 
async def generate_story(file: UploadFile = File(...)): 
    session_id = str(uuid.uuid4())

    # 1. Save File
    file_ext = os.path.splitext(file.filename)[1].lower()
    # Default to .txt if extension is missing/weird, or validate strict
    if file_ext not in [".pdf", ".docx", ".pptx", ".txt"]:
        # Fallback for octet-stream or others if needed, or just allow it
        pass 
    
    file_path = f"uploads/{session_id}{file_ext}"
    with open(file_path, "wb") as f: 
        f.write(await file.read())

    # 2. Generate Story
    story_data = gemini.process_file_to_story(file_path)
    if not story_data: 
        raise HTTPException(status_code=500, detail="Failed to generate story")

    story_data["story_id"] = session_id 
    story_seed = random.randint(0, 99999999) 
    story_data["visual_seed"] = story_seed

    # 3. Generate Media
    final_scenes = []
    for i, scene in enumerate(story_data['scenes']):
        full_prompt = f"{scene['image_description']}. Character details: {scene.get('character_details', '')}"
        img_bytes = gemini.generate_image(full_prompt, seed=story_seed)
    
        img_filename = f"outputs/{session_id}_scene_{i}.png"
        if img_bytes:
            with open(img_filename, "wb") as f:
                f.write(img_bytes)
        audio_bytes = gemini.generate_voiceover(scene['text'])
        audio_filename = f"outputs/{session_id}_scene_{i}.wav"
        if audio_bytes:
            with open(audio_filename, "wb") as f:
                f.write(audio_bytes)
    
        scene['image_url'] = f"/outputs/{session_id}_scene_{i}.png"
        scene['audio_url'] = f"/outputs/{session_id}_scene_{i}.wav"
        final_scenes.append(scene)
    story_data["scenes"] = final_scenes
    save_path = f"saved_stories/{session_id}.json"
    with open(save_path, "w") as f:
        json.dump(story_data, f)
    return story_data
    
@app.get("/api/load/{story_id}") 
async def load_story(story_id: str): 
    try: 
        with open(f"saved_stories/{story_id}.json", "r") as f: 
            return json.load(f) 
    except FileNotFoundError: 
        raise HTTPException(status_code=404, detail="Story not found")