"""
Voice Generator Service
Uses Piper TTS locally or ElevenLabs API for voiceovers.
Handles audio generation and caching asynchronously, with concurrency limits.
"""
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

import aiofiles
import httpx

from config import Config
from services.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class VoiceGenerator:
    """Generates expressive voiceovers for scene narration."""

    def __init__(self):
        self.use_local = Config.USE_LOCAL_TTS
        self.elevenlabs_key = Config.ELEVENLABS_API_KEY
        self.piper_model = Config.PIPER_MODEL
        self.output_dir = Path("outputs/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache = CacheManager()

        # Maps generic styles to specific ElevenLabs voice IDs
        self.voice_profiles = {
            "expressive_child": "Rachel", # Premade voice ID
            "storyteller": "Bella",      # Premade voice ID
            "friendly": "Antoni",      # Premade voice ID
            "energetic": "Josh",         # Premade voice ID
        }
        # Concurrency limit for API calls
        self.semaphore = asyncio.Semaphore(2)

    async def generate_voiceovers(self, screenplay, voice_style: str = "expressive_child") -> List[Dict]:
        """Generates voiceover audio for all scenes with a concurrency limit."""
        tasks = [
            self.generate_single_voiceover(
                text=scene.narration,
                voice_style=voice_style,
                scene_number=scene.scene_number
            )
            for scene in screenplay.scenes
        ]
        
        audio_paths = await asyncio.gather(*tasks)

        return [
            {
                "scene_number": screenplay.scenes[i].scene_number,
                "audio_path": path,
                "duration": self._estimate_duration(screenplay.scenes[i].narration),
            }
            for i, path in enumerate(audio_paths)
        ]

    async def generate_single_voiceover(self, text: str, voice_style: str, scene_number: int) -> str:
        """Generates a single voiceover, checking cache first."""
        cache_key_params = {"text": text, "voice_style": voice_style}
        
        cached_audio = await self.cache.get("audio", **cache_key_params)
        if cached_audio:
            logger.info(f"Cache hit for audio scene {scene_number}")
            return cached_audio

        logger.info(f"Cache miss for audio scene {scene_number}. Generating new audio.")
        
        async with self.semaphore:
            audio_path = None
            if self.use_local:
                audio_path = await self._generate_with_piper(text, scene_number)
            
            if not audio_path and self.elevenlabs_key:
                audio_path = await self._generate_with_elevenlabs(text, voice_style, scene_number)

            final_path = audio_path or self._create_placeholder(scene_number)
            
            if audio_path: # Only cache successful results
                await self.cache.set("audio", final_path, **cache_key_params)
                
            return final_path

    def _run_piper_sync(self, text: str, audio_path: Path):
        """Synchronous helper to run the Piper TTS command."""
        command = ["piper", "--model", self.piper_model, "--output_file", str(audio_path)]
        subprocess.run(command, input=text.encode(), check=True, capture_output=True)

    async def _generate_with_piper(self, text: str, scene_number: int) -> Optional[str]:
        """Generates audio using the local Piper TTS CLI tool."""
        logger.info(f"Generating audio for scene {scene_number} with Piper TTS.")
        audio_path = self.output_dir / f"scene_{scene_number}.wav"
        
        try:
            await asyncio.to_thread(self._run_piper_sync, text, audio_path)
            return str(audio_path)
        except FileNotFoundError:
            logger.error("`piper` command not found. Is piper-tts installed and in the system's PATH?")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Piper TTS failed with exit code {e.returncode}: {e.stderr.decode()}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Piper TTS generation: {e}", exc_info=True)
            return None

    async def _generate_with_elevenlabs(self, text: str, voice_style: str, scene_number: int) -> Optional[str]:
        """Generates audio using the ElevenLabs API."""
        logger.info(f"Generating audio for scene {scene_number} with ElevenLabs.")
        voice_id = self.voice_profiles.get(voice_style, "21m00Tcm4TlvDq8ikWAM")  # Default to Rachel
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {"Accept": "audio/mpeg", "xi-api-key": self.elevenlabs_key}
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Use a newer, compatible model
            "voice_settings": {"stability": 0.55, "similarity_boost": 0.75},
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                audio_path = self.output_dir / f"scene_{scene_number}.mp3"
                async with aiofiles.open(audio_path, "wb") as f:
                    await f.write(response.content)
                
                return str(audio_path)
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs API request failed: {e.response.status_code} - {e.response.text}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"ElevenLabs generation failed: {e}", exc_info=True)
            return None

    def _create_placeholder(self, scene_number: int) -> str:
        """Creates a placeholder audio path when generation fails."""
        return f"/api/placeholder/audio_{scene_number}.mp3"

    def _estimate_duration(self, text: str) -> float:
        """Estimates audio duration based on text length."""
        if not text:
            return 0.0
        word_count = len(text.split())
        words_per_second = 150 / 60  # Approx. 2.5 words per second
        duration = word_count / words_per_second
        return round(max(1.0, duration), 2)  # Ensure a minimum duration
