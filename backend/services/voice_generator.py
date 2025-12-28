"""
Voice Generator Service
Uses ElevenLabs or similar TTS to generate expressive voiceovers
"""

import os
import asyncio
import httpx
from typing import List, Dict
from pathlib import Path


class VoiceGenerator:
    """Generates expressive voiceovers for scene narration"""
    
    def __init__(self):
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.output_dir = Path("outputs/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
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
        if self.elevenlabs_key:
            return await self._generate_with_elevenlabs(text, voice_style, scene_number)
        else:
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
