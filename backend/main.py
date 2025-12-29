from fastapi import FastAPI, UploadFile, File, HTTPException
import os, uuid, json, random
from services.gemini_service import GeminiService
app = FastAPI() 
gemini = GeminiService()

# Absolute paths for Docker Bind Mounts
UPLOAD_DIR = "/app/uploads" 
OUTPUT_DIR = "/app/outputs" 
STORAGE_DIR = "/app/saved_stories" 
for d in [UPLOAD_DIR, OUTPUT_DIR, STORAGE_DIR]: 
    os.makedirs(d, exist_ok=True)

@app.post("/api/upload") 
async def generate_story(file: UploadFile = File(...)): 
    session_id = str(uuid.uuid4()) 
    file_path = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    story_data = gemini.process_file_to_story(file_path)
    if not story_data:
        raise HTTPException(status_code=500, detail="Gemini failed to generate story JSON")

    story_seed = random.randint(0, 999999)
    scenes = story_data.get("scenes", [])
    for i, scene in enumerate(scenes): 
        # Image Generation 
        img_prompt = scene.get("image_description", "storybook illustration") 
        img_bytes = gemini.generate_image(img_prompt, seed=story_seed) 
        if img_bytes: 
            fname = f"{session_id}_img_{i}.png" 
            with open(os.path.join(OUTPUT_DIR, fname), "wb") as f: 
                f.write(img_bytes) 
            scene["image_url"] = f"/outputs/{fname}"

        # Audio Generation
        audio_bytes = gemini.generate_voiceover(scene.get("text", ""))
        if audio_bytes:
            aname = f"{session_id}_aud_{i}.wav"
            with open(os.path.join(OUTPUT_DIR, aname), "wb") as f:
                f.write(audio_bytes)
            scene["audio_url"] = f"/outputs/{aname}"

    story_data["story_id"] = session_id
    with open(os.path.join(STORAGE_DIR, f"{session_id}.json"), "w") as f:
        json.dump(story_data, f)
        
    return story_data