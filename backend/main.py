from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from services.gemini_service import GeminiService
import os
import json
import uuid
import random
import aiofiles

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all necessary folders
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
os.makedirs("saved_stories", exist_ok=True)

# Serve static files (images/audio)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

try:
    gemini = GeminiService()
except ValueError as e:
    print(f"FATAL: Failed to initialize GeminiService: {e}")
    gemini = None

@app.post("/api/generate")
async def generate_story(file: UploadFile = File(...)):
    if not gemini:
        raise HTTPException(status_code=500, detail="Gemini service is not initialized. Check API key.")

    session_id = str(uuid.uuid4())
    
    # 1. Save File with CORRECT Extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".pdf", ".docx", ".pptx", ".txt"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_path = f"uploads/{session_id}{file_ext}"

    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await file.read())
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # 2. Generate Story (Pass file path to service)
    story_data = gemini.process_file_to_story(file_path)
    if not story_data:
        raise HTTPException(status_code=500, detail="Failed to generate story")
    
    story_data["story_id"] = session_id

    # 3. Generate Global Seed (The secret to consistent characters)
    story_seed = random.randint(0, 99999999)
    story_data["visual_seed"] = story_seed

    # 4. Generate Media for Each Scene
    final_scenes = []
    for i, scene in enumerate(story_data['scenes']):
        # Image: Combine description with character details + SEED
        full_prompt = f"{scene['image_description']}. Character details: {scene.get('character_details', '')}"
        img_bytes = gemini.generate_image(full_prompt, seed=story_seed)
        
        img_filename = f"outputs/{session_id}_scene_{i}.png"
        if img_bytes:
            try:
                async with aiofiles.open(img_filename, "wb") as f:
                    await f.write(img_bytes)
                scene['image_url'] = f"/outputs/{session_id}_scene_{i}.png"
            except IOError as e:
                print(f"Error saving image for scene {i}: {e}")
                scene['image_url'] = None # Or a placeholder
        else:
            scene['image_url'] = None

        # Audio: Generate Voiceover
        audio_bytes = gemini.generate_voiceover(scene['text'])
        audio_filename = f"outputs/{session_id}_scene_{i}.wav"
        if audio_bytes:
            try:
                async with aiofiles.open(audio_filename, "wb") as f:
                    await f.write(audio_bytes)
                scene['audio_url'] = f"/outputs/{session_id}_scene_{i}.wav"
            except IOError as e:
                print(f"Error saving audio for scene {i}: {e}")
                scene['audio_url'] = None
        else:
            scene['audio_url'] = None
        
        final_scenes.append(scene)

    story_data["scenes"] = final_scenes
    
    # 5. Save to Disk (Persistence)
    save_path = f"saved_stories/{session_id}.json"
    try:
        async with aiofiles.open(save_path, "w") as f:
            await f.write(json.dumps(story_data, indent=2))
    except IOError as e:
        print(f"Error saving story JSON: {e}")
        # Not a fatal error for the user, so we don't raise HTTPException
        
    # Clean up uploaded file
    try:
        os.remove(file_path)
    except OSError as e:
        print(f"Error removing uploaded file {file_path}: {e}")

    return story_data

@app.get("/api/load/{story_id}")
async def load_story(story_id: str):
    """Loads a saved story JSON to avoid regenerating credits."""
    try:
        async with aiofiles.open(f"saved_stories/{story_id}.json", "r") as f:
            content = await f.read()
            return JSONResponse(content=json.loads(content))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Story not found")
    except (IOError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Error reading story file: {e}")
