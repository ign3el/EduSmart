"""
EduSmart Backend - Main FastAPI Application
Handles file uploads, AI orchestration, and content generation
Supports both API-based and local open-source AI models
"""
import uvicorn
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pathlib import Path

from services.document_processor import DocumentProcessor
from services.script_generator import ScriptGenerator
from services.image_generator import ImageGenerator
from services.voice_generator import VoiceGenerator
from services.scene_assembler import SceneAssembler
from services.cache_manager import CacheManager
from models.story import StoryRequest, StoryResponse
from config import Config

# Configure logging
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="EduSmart API",
    description="AI-Powered Educational Storybook Generator",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
script_generator = ScriptGenerator()
image_generator = ImageGenerator()
voice_generator = VoiceGenerator()
scene_assembler = SceneAssembler()
cache_manager = CacheManager()

# Create necessary directories
UPLOAD_DIR = Path(Config.UPLOAD_DIR)
OUTPUT_DIR = Path(Config.OUTPUT_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "EduSmart API",
        "version": "1.0.0",
        "config": Config.get_info()
    }


@app.get("/api/config")
async def get_config():
    """Get current configuration and service status"""
    cache_health = await cache_manager.health_check()
    
    return {
        "config": Config.get_info(),
        "cache": {
            "enabled": Config.USE_CACHE,
            "status": "healthy" if cache_health else "offline",
            "redis_url": Config.REDIS_URL
        }
    }


@app.post("/api/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    grade_level: int = 1,
    avatar_type: str = "wizard"
):
    """
    Upload a PDF or DOCX file and initiate story generation
    
    Args:
        file: PDF or DOCX file containing educational content
        grade_level: Target grade level (1-7)
        avatar_type: Character type (wizard, robot, squirrel, etc.)
    
    Returns:
        Story ID and initial processing status
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and DOCX files are supported"
            )
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text from document
        extracted_text = await document_processor.process(file_path)
        
        # Generate unique story ID
        story_id = f"story_{hash(file.filename + str(grade_level))}"
        
        return {
            "story_id": story_id,
            "filename": file.filename,
            "extracted_length": len(extracted_text),
            "status": "processing",
            "message": "Document uploaded successfully. Story generation started."
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error during file upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred during file upload.")


@app.post("/api/generate-story/{story_id}")
async def generate_story(
    story_id: str,
    request: StoryRequest
):
    """
    Generate complete interactive story with scenes, images, and audio
    
    Args:
        story_id: Unique story identifier
        request: Story generation parameters
    
    Returns:
        Complete story with all generated assets
    """
    try:
        # Step 1: Generate screenplay from document text
        screenplay = await script_generator.generate_screenplay(
            text=request.document_text,
            grade_level=request.grade_level,
            avatar_type=request.avatar_type
        )
        
        # Step 2: Generate images for each scene
        scene_images = await image_generator.generate_scenes(
            screenplay=screenplay,
            avatar_type=request.avatar_type,
            style="anime"
        )
        
        # Step 3: Generate voiceovers for each scene
        scene_audio = await voice_generator.generate_voiceovers(
            screenplay=screenplay,
            voice_style="expressive_child"
        )
        
        # Step 4: Assemble everything into timeline
        story_timeline = await scene_assembler.assemble(
            screenplay=screenplay,
            images=scene_images,
            audio=scene_audio,
            story_id=story_id
        )
        
        return {
            "story_id": story_id,
            "status": "completed",
            "timeline": story_timeline,
            "total_scenes": len(screenplay.scenes),
            "message": "Story generated successfully"
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error generating story {story_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred during story generation.")


@app.get("/api/story/{story_id}")
async def get_story(story_id: str):
    """
    Retrieve a generated story by ID
    
    Args:
        story_id: Unique story identifier
    
    Returns:
        Complete story data
    """
    # TODO: Implement story retrieval from database/storage
    return {"story_id": story_id, "status": "available"}


@app.get("/api/avatars")
async def get_available_avatars():
    """
    Get list of available avatar types for character consistency
    
    Returns:
        List of avatar configurations
    """
    return {
        "avatars": [
            {"id": "wizard", "name": "Wise Wizard", "description": "A magical teacher"},
            {"id": "robot", "name": "Friendly Robot", "description": "A helpful AI companion"},
            {"id": "squirrel", "name": "Smart Squirrel", "description": "A clever forest friend"},
            {"id": "astronaut", "name": "Space Explorer", "description": "A cosmic guide"},
            {"id": "dinosaur", "name": "Dino Teacher", "description": "A prehistoric professor"},
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
