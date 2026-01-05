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
        self.api_key = os.getenv("CHATTERBOX_API_KEY", None)
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
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
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
                headers=headers,
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

    async def generate_audio_batch(self, texts: list[str], voice: str = "en-US-JennyNeural") -> list[Optional[bytes]]:
        """
        Generate TTS audio for multiple texts in parallel batches.
        
        Args:
            texts: List of text strings to synthesize
            voice: Voice identifier
        
        Returns:
            List of audio bytes (MP3) or None for failures
        """
        # Process in batches of 3 to avoid overwhelming the service
        batch_size = 3
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_tasks = [self.generate_audio(text, voice) for text in batch]
            
            # Run batch in parallel
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle results
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"✗ Batch item failed: {result}")
                    results.append(None)
                else:
                    results.append(result)
            
            # Brief pause between batches
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)
        
        return results

    async def generate_audio_optimized(self, text: str, voice: str = "en-US-JennyNeural", is_mobile: bool = False) -> Optional[bytes]:
        """
        Generate TTS with mobile optimization (lower bitrate for faster streaming).
        
        Args:
            text: Text to synthesize
            voice: Voice identifier
            is_mobile: Whether to optimize for mobile (lower bitrate)
        
        Returns:
            Audio bytes (MP3) or None on failure
        """
        try:
            selected_voice = self._detect_language_and_voice(text, voice)
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            # Mobile optimization: lower bitrate for faster streaming
            bitrate = 64 if is_mobile else 128
            
            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/tts",
                json={
                    "text": text,
                    "voice": selected_voice,
                    "rate": 0.9,
                    "format": "mp3",
                    "bitrate": bitrate  # Mobile gets 64kbps, desktop gets 128kbps
                },
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                audio_bytes = response.content
                print(f"✓ Chatterbox TTS {'(mobile)' if is_mobile else ''}: {len(audio_bytes)} bytes @ {bitrate}kbps")
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
