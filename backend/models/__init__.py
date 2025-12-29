"""
Models Package

Data models for the EduSmart application using Pydantic for validation.

Models:
    - Scene: Individual scene with visual description, narration, and learning point
    - Screenplay: Collection of scenes forming the complete story
    - StoryRequest: API request model for story generation
    - StoryResponse: API response model with generated story data
    - AvatarType: Enum of available character types
"""

from .story import Scene, Screenplay, StoryRequest, StoryResponse

__all__ = ['Scene', 'Screenplay', 'StoryRequest', 'StoryResponse']
