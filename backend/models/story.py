"""
Data models for story generation
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class AvatarType(str, Enum):
    """Available avatar/character types"""
    WIZARD = "wizard"
    ROBOT = "robot"
    SQUIRREL = "squirrel"
    ASTRONAUT = "astronaut"
    DINOSAUR = "dinosaur"


class Scene(BaseModel):
    """Individual scene in the screenplay"""
    scene_number: int
    visual_description: str = Field(description="What appears on screen")
    narration: str = Field(description="Character dialogue/narration")
    learning_point: str = Field(description="Key educational concept")


class Screenplay(BaseModel):
    """Complete screenplay with all scenes"""
    scenes: List[Scene]
    
    @property
    def total_scenes(self) -> int:
        return len(self.scenes)


class StoryRequest(BaseModel):
    """Request model for story generation"""
    document_text: str = Field(description="Extracted text from uploaded document")
    grade_level: int = Field(ge=1, le=7, description="Target grade level (1-7)")
    avatar_type: str = Field(default="wizard", description="Character type for narration")
    style: str = Field(default="anime", description="Visual art style")


class StoryResponse(BaseModel):
    """Response model for completed story"""
    story_id: str
    status: str
    timeline: dict
    total_scenes: int
    total_duration: Optional[float] = None
    message: str
