"""
Image Generator Service
Uses Stable Diffusion locally (via diffusers) or cloud APIs (Stability AI).
Handles asynchronous initialization and generation.
"""
import asyncio
import base64
import logging
from pathlib import Path
from typing import List, Dict, Optional

import httpx
from config import Config
from services.cache_manager import CacheManager

try:
    from diffusers import StableDiffusionPipeline
    import torch
except ImportError:
    StableDiffusionPipeline = None
    torch = None

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generates consistent character images for each scene asynchronously."""

    _pipeline: Optional[StableDiffusionPipeline] = None
    _pipeline_initializing = False

    def __init__(self):
        self.use_local = Config.USE_LOCAL_IMAGE_GEN
        self.stability_key = Config.STABILITY_API_KEY
        self.output_dir = Path("outputs/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache = CacheManager()

        self.character_seeds = {
            "wizard": "elderly wizard with purple robes and long white beard, glowing staff",
            "robot": "friendly round robot with blue metallic body and glowing eyes",
            "squirrel": "cheerful brown squirrel with bushy tail and bright eyes",
            "astronaut": "young astronaut in white spacesuit with clear helmet",
            "dinosaur": "friendly green dinosaur with small arms and big smile",
        }

    async def _initialize_pipeline(self):
        """Initializes the local Stable Diffusion pipeline asynchronously."""
        if self._pipeline or not self.use_local or self._pipeline_initializing:
            return

        if StableDiffusionPipeline is None or torch is None:
            logger.error("Diffusers or PyTorch not installed. Cannot use local image generation.")
            self.use_local = False
            return

        self._pipeline_initializing = True
        logger.info(f"Loading Stable Diffusion model '{Config.STABLE_DIFFUSION_MODEL}'...")

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32

            loop = asyncio.get_event_loop()
            pipeline = await loop.run_in_executor(
                None,
                lambda: StableDiffusionPipeline.from_pretrained(Config.STABLE_DIFFUSION_MODEL, torch_dtype=dtype)
            )
            pipeline.to(device)

            if not Config.ENABLE_SAFETY_CHECKER:
                pipeline.safety_checker = None

            self._pipeline = pipeline
            logger.info(f"Stable Diffusion pipeline ready on {device}.")
        except Exception as e:
            logger.error(f"Failed to initialize local diffusers pipeline: {e}", exc_info=True)
            self.use_local = False
        finally:
            self._pipeline_initializing = False

    async def generate_scenes(self, screenplay, avatar_type: str, style: str = "anime") -> List[Dict[str, str]]:
        """Generates images for all scenes with a consistent character."""
        character_seed = self.character_seeds.get(avatar_type, f"{avatar_type} character")
        
        tasks = [
            self.generate_single_image(
                visual_description=scene.visual_description,
                character_seed=character_seed,
                style=style,
                scene_number=scene.scene_number,
            )
            for scene in screenplay.scenes
        ]
        image_paths = await asyncio.gather(*tasks)

        return [
            {
                "scene_number": screenplay.scenes[i].scene_number,
                "image_path": path,
                "description": screenplay.scenes[i].visual_description,
            }
            for i, path in enumerate(image_paths)
        ]

    async def generate_single_image(self, visual_description: str, character_seed: str, style: str, scene_number: int) -> str:
        """Generates a single image, checking cache first."""
        cache_key_params = {
            "visual_description": visual_description,
            "character_seed": character_seed,
            "style": style,
        }
        
        cached_image = await self.cache.get("image", **cache_key_params)
        if cached_image:
            return cached_image

        full_prompt = f"{style} art style, {character_seed}, {visual_description}, educational illustration, bright colors, child-friendly"

        image_path = None
        if self.use_local:
            await self._initialize_pipeline()  # Ensure pipeline is ready
            if self._pipeline:
                image_path = await self._generate_with_diffusers(full_prompt, scene_number)
        
        if not image_path and self.stability_key:
            image_path = await self._generate_with_stability(full_prompt, scene_number)

        final_path = image_path or self._create_placeholder(scene_number)
        
        if image_path: # Only cache successful generations
             await self.cache.set("image", final_path, **cache_key_params)

        return final_path

    def _save_image_sync(self, image, path):
        """Synchronous helper to save an image."""
        image.save(path)

    async def _generate_with_diffusers(self, prompt: str, scene_number: int) -> Optional[str]:
        """Generates an image using the local Stable Diffusion pipeline."""
        logger.info(f"Generating image for scene {scene_number} with local Stable Diffusion.")
        try:
            loop = asyncio.get_event_loop()
            
            def _inference():
                return self._pipeline(
                    prompt,
                    num_inference_steps=Config.IMAGE_INFERENCE_STEPS,
                    guidance_scale=7.5,
                ).images[0]

            image = await loop.run_in_executor(None, _inference)
            
            image_path = self.output_dir / f"scene_{scene_number}.png"
            await loop.run_in_executor(None, self._save_image_sync, image, image_path)

            return str(image_path)
        except Exception as e:
            logger.error(f"Local diffusers generation failed: {e}", exc_info=True)
            return None

    async def _generate_with_stability(self, prompt: str, scene_number: int) -> Optional[str]:
        """Generates an image using the Stability AI API."""
        logger.info(f"Generating image for scene {scene_number} with Stability AI.")
        url = "https://api.stability.ai/v2/generation/stable-image-core/generate/sd3"
        
        headers = {
            "Authorization": f"Bearer {self.stability_key}",
            "Accept": "application/json",
        }
        
        payload = {
            "prompt": prompt,
            "output_format": "png",
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(url, headers=headers, files={"none": ''}, data=payload)
                response.raise_for_status()
                
                image_path = self.output_dir / f"scene_{scene_number}.png"
                image_path.write_bytes(response.content)

                return str(image_path)
        except httpx.HTTPStatusError as e:
            logger.error(f"Stability AI API request failed with status {e.response.status_code}: {e.response.text}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Stability AI generation failed: {e}", exc_info=True)
            return None

    def _create_placeholder(self, scene_number: int) -> str:
        """Creates a placeholder image path for when generation fails."""
        # This path can be handled by the frontend to show a placeholder UI
        return f"/api/placeholder/scene_{scene_number}.png"