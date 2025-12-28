"""
Voice Generator Service
Uses Piper TTS locally or ElevenLabs API for voiceovers
"""

import os
import asyncio
import httpx
from typing import List, Dict
from pathlib import Path

try:
    import piper
except ImportError:
    piper = None

from config import Config
from services.cache_manager import CacheManager


class VoiceGenerator:
    """Generates expressive voiceovers for scene narration"""
    
    def __init__(self):
        self.use_local = Config.USE_LOCAL_TTS
        self.elevenlabs_key = Config.ELEVENLABS_API_KEY
        self.piper_model = Config.PIPER_MODEL
        self.output_dir = Path("outputs/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache = CacheManager()
        
        # Voice profiles for different styles
        self.voice_profiles = {
            "expressive_child": "Rachel",  # ElevenLabs voice ID
            "storyteller": "Bella",
            "friendly": "Antoni",
            "energetic": "Josh"
        }
    
    async def generate_voiceovers(
        self,
        screenplay,
        voice_style: str = "expressive_child"
    ) -> List[Dict[str, str]]:
        """
        Generate voiceover audio for all scenes
        
        Args:
            screenplay: Screenplay object with scenes
            voice_style: Voice profile to use
        
        Returns:
            List of audio paths for each scene
        """
        scene_audio = []
        
        for scene in screenplay.scenes:
            audio_path = await self.generate_single_voiceover(
                text=scene.narration,
                voice_style=voice_style,
                scene_number=scene.scene_number
            )
            
            scene_audio.append({
                "scene_number": scene.scene_number,
                "audio_path": audio_path,
                "duration": await self._estimate_duration(scene.narration)
            })
        
        return scene_audio
    
    async def generate_single_voiceover(
        self,
        text: str,
        voice_style: str,
        scene_number: int
    ) -> str:
        """
        Generate a single voiceover audio file
        
        Args:
            text: Narration text to convert to speech
            voice_style: Voice profile identifier
            scene_number: Scene identifier
        
        Returns:
            Path to generated audio file
        """
        # Check cache
        cached_audio = await self.cache.get(
            "audio",
            text=text,
            voice_style=voice_style
        )
        if cached_audio and cached_audio != f"/api/placeholder/audio_{scene_number}.mp3":
            return cached_audio
        
        # Generate new audio
        if self.use_local and piper:
            return await self._generate_with_piper(text, scene_number)
        elif self.elevenlabs_key:
            return await self._generate_with_elevenlabs(text, voice_style, scene_number)
        else:
            return self._create_placeholder(scene_number)
    
    async def _generate_with_piper(self, text: str, scene_number: int) -> str:
        """Generate audio using local Piper TTS"""
        try:
            # Run TTS in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            audio_path = self.output_dir / f"scene_{scene_number}.wav"
            
            # Use piper-tts command line tool
            import subprocess
            
            await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["piper", "--model", self.piper_model, "--output_file", str(audio_path)],
                    input=text.encode(),
                    check=True
                )
            )
            
            # Cache the path
            await self.cache.set(
                "audio",
                str(audio_path),
                text=text,
                voice_style=""
            )
            
            return str(audio_path)
        
        except Exception as e:
            print(f"Piper TTS error: {e}")
            return self._create_placeholder(scene_number)
    
    async def _generate_with_elevenlabs(
        self,
        text: str,
        voice_style: str,
        scene_number: int
    ) -> str:
        """Generate audio using ElevenLabs API"""
        
        voice_id = self.voice_profiles.get(voice_style, "Rachel")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_key
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                # Save the audio file
                audio_path = self.output_dir / f"scene_{scene_number}.mp3"
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                
                return str(audio_path)
        
        except Exception as e:
            print(f"ElevenLabs error: {e}")
            return self._create_placeholder(scene_number)
    
    def _create_placeholder(self, scene_number: int) -> str:
        """Create placeholder audio path when API is not available"""
        return f"/api/placeholder/audio_{scene_number}.mp3"
    
    async def _estimate_duration(self, text: str) -> float:
        """
        Estimate audio duration based on text length
        Rough estimate: ~150 words per minute
        
        Args:
            text: Narration text
        
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        words_per_second = 150 / 60  # ~2.5 words per second
        duration = word_count / words_per_second
        return round(duration, 2)
