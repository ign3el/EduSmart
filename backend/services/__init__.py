"""
Backend Services Package

This package contains all the core AI services for EduSmart:

Services:
    - gemini_service: Unified service for text, image, and audio generation

All services are initialized in main.py and called via API endpoints.
"""

"""
Backend Services Package

This package contains all the core AI services for EduSmart.
"""

from .story_service import GeminiService

__all__ = [
    'GeminiService',
]
