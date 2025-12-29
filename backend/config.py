"""
Configuration Module
Manages service selection (API vs Local) and model settings
"""

import os
from enum import Enum


class ServiceMode(str, Enum):
    """Service mode selection"""
    API = "api"  # Use paid APIs
    LOCAL = "local"  # Use local models


class Config:
    """Application configuration"""
    
    # Service mode
    SERVICE_MODE = os.getenv("SERVICE_MODE", "local").lower()  # "api" or "local"
    
    # Text Generation Service
    USE_LOCAL_LLM = SERVICE_MODE == "local"
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # mistral, llama2, neural-chat
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Image Generation Service
    USE_LOCAL_IMAGE_GEN = SERVICE_MODE == "local"
    STABLE_DIFFUSION_MODEL = os.getenv("STABLE_DIFFUSION_MODEL", 
                                       "runwayml/stable-diffusion-v1-5")
    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")
    ENABLE_SAFETY_CHECKER = os.getenv("ENABLE_SAFETY_CHECKER", "false").lower() == "true"
    IMAGE_INFERENCE_STEPS = int(os.getenv("IMAGE_INFERENCE_STEPS", "25"))
    
    # Voice Generation Service
    USE_LOCAL_TTS = SERVICE_MODE == "local"
    PIPER_MODEL = os.getenv("PIPER_MODEL", "en_US-ryan-medium")  # voice model name
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    
    # Caching
    USE_CACHE = os.getenv("USE_CACHE", "true").lower() == "true"
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CACHE_TTL = int(os.getenv("CACHE_TTL", 86400))  # 24 hours
    
    # File handling
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))  # 10MB
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def get_info(cls) -> dict:
        """Get current configuration info"""
        return {
            "service_mode": cls.SERVICE_MODE,
            "text_generation": {
                "type": "local_ollama" if cls.USE_LOCAL_LLM else "openai",
                "model": cls.OLLAMA_MODEL if cls.USE_LOCAL_LLM else cls.OPENAI_MODEL,
                "endpoint": cls.OLLAMA_BASE_URL if cls.USE_LOCAL_LLM else "api.openai.com"
            },
            "image_generation": {
                "type": "local_diffusers" if cls.USE_LOCAL_IMAGE_GEN else "stability_ai",
                "model": cls.STABLE_DIFFUSION_MODEL if cls.USE_LOCAL_IMAGE_GEN else "stable-diffusion-3"
            },
            "voice_generation": {
                "type": "local_piper" if cls.USE_LOCAL_TTS else "elevenlabs",
                "model": cls.PIPER_MODEL if cls.USE_LOCAL_TTS else "professional"
            },
            "caching": {
                "enabled": cls.USE_CACHE,
                "redis_url": cls.REDIS_URL,
                "ttl_seconds": cls.CACHE_TTL
            }
        }
