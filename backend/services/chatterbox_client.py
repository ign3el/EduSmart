"""
Chatterbox TTS HTTP Client
Self-hosted TTS service replacing Edge TTS
"""
import os
import requests
import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class ChatterboxClient:
    def __init__(self):
        # Chatterbox TTS endpoint (self-hosted)
        self.base_url = os.getenv("CHATTERBOX_URL", "http://localhost:8001")
        self.timeout = 60  # Longer timeout for TTS generation
    
    def _detect_language_and_voice(self, text: str, default_voice: str = "en-US-JennyNeural") -> str:
        """Detect language from text and return appropriate voice."""
        # Check for Arabic characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F')
        total_chars = sum(1 for c in text if c.isalpha())
        
        if total_chars > 0 and arabic_chars / total_chars > 0.3:
            return "ar-SA-HamedNeural"  # Arabic voice
        
        return default_voice
    
    async def generate_audio(self, text: str, voice: str = "en-US-JennyNeural") -> Optional[bytes]:
        """
        Generate TTS audio via Chatterbox HTTP API.
        
        Args:
            text: Text to synthesize
            voice: Voice identifier (compatible with Edge TTS names)
        
        Returns:
            Audio bytes (MP3) or None on failure
        """
        try:
            # Auto-detect language
            selected_voice = self._detect_language_and_voice(text, voice)
            
            # Call Chatterbox API
            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/tts",
                json={
                    "text": text,
                    "voice": selected_voice,
                    "rate": 0.9,  # Slightly slower for clarity
                    "format": "mp3"
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                audio_bytes = response.content
                print(f"✓ Chatterbox TTS generated: {len(audio_bytes)} bytes")
                return audio_bytes
            else:
                print(f"✗ Chatterbox TTS failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("✗ Chatterbox TTS timeout")
            return None
        except Exception as e:
            print(f"✗ Chatterbox TTS error: {e}")
            return None

# Global instance
chatterbox = ChatterboxClient()
