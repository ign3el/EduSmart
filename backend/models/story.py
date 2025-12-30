from pydantic import BaseModel
from typing import List, Optional

# --- Internal Data Structures ---
class QuizItem(BaseModel):
    question: str
    options: List[str]
    answer: str
    explanation: str  # Added explanation for review mode

class Scene(BaseModel):
    text: str
    image_description: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None

# --- API Request/Response Models ---
class StoryRequest(BaseModel):
    """What the frontend sends when requesting a story."""
    grade_level: str
    topic: Optional[str] = None

class StorySchema(BaseModel):
    """The structure Gemini must follow for its JSON output."""
    title: str
    scenes: List[Scene]
    quiz: List[QuizItem]

class StoryResponse(BaseModel):
    """The final object sent back to the frontend."""
    job_id: str
    status: str
    progress: int
    result: Optional[StorySchema] = None

class Screenplay(BaseModel):
    """Used if you want a flattened version of the story for internal processing."""
    title: str
    content: List[str]