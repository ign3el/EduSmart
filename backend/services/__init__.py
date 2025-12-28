"""
Backend Services Package

This package contains all the core AI services for EduStory:

Services:
    - document_processor: Extracts text from PDF and DOCX files
    - script_generator: Converts content into interactive screenplay
    - image_generator: Generates consistent anime/cartoon-style images
    - voice_generator: Generates expressive voiceovers for narration
    - scene_assembler: Combines screenplay, images, and audio into timeline
    - cache_manager: Handles Redis-based caching of generated content

All services are initialized in main.py and called via API endpoints.
"""

from .document_processor import DocumentProcessor
from .script_generator import ScriptGenerator
from .image_generator import ImageGenerator
from .voice_generator import VoiceGenerator
from .scene_assembler import SceneAssembler
from .cache_manager import CacheManager

__all__ = [
    'DocumentProcessor',
    'ScriptGenerator',
    'ImageGenerator',
    'VoiceGenerator',
    'SceneAssembler',
    'CacheManager',
]
