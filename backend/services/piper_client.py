"""
Piper TTS HTTP Client
"""
import os
import requests
import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class PiperClient:
    def __init__(self):
        # Piper TTS endpoint (self-hosted)
        self.base_url = os.getenv("PIPER_URL", "http://localhost:5000")
        self.api_key = os.getenv("PIPER_API_KEY", None) # For future use if API is secured
        self.timeout = 90  # Increased timeout for potentially longer generations

    async def generate_audio(self, text: str, language: str, speed: float, silence: float) -> Optional[bytes]:
        """
        Generate TTS audio via Piper HTTP API.
        
        Args:
            text: Text to synthesize.
            language: Language code (e.g., 'en', 'ar').
            speed: Playback speed (e.g., 1.0).
            silence: Silence in seconds between sentences.
        
        Returns:
            Audio bytes (WAV) or None on failure.
        """
        try:
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            # Prepare payload for Piper API
            payload = {
                "text": text,
                "language": language,
                "speed": speed,
                "silence": silence,
            }
            
            # Call Piper API
            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/tts",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                audio_bytes = response.content
                print(f"✓ Piper TTS generated: {len(audio_bytes)} bytes")
                return audio_bytes
            else:
                print(f"✗ Piper TTS failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("✗ Piper TTS timeout")
            return None
        except Exception as e:
            print(f"✗ Piper TTS error: {e}")
            return None

# Global instance
piper_tts = PiperClient()
