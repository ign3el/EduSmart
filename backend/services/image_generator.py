"""
Image Generator Service
Uses Stable Diffusion or DALL-E to generate consistent anime-style scene images
"""

import os
import asyncio
import httpx
from typing import List, Dict
from pathlib import Path


class ImageGenerator:
    """Generates consistent character images for each scene"""
    
    def __init__(self):
        self.stability_key = os.getenv("STABILITY_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.output_dir = Path("outputs/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Character seed tokens for consistency
        self.character_seeds = {
            "wizard": "elderly wizard with purple robes and long white beard, glowing staff",
            "robot": "friendly round robot with blue metallic body and glowing eyes",
            "squirrel": "cheerful brown squirrel with bushy tail and bright eyes",
            "astronaut": "young astronaut in white spacesuit with clear helmet",
            "dinosaur": "friendly green dinosaur with small arms and big smile",
        }
    
    async def generate_scenes(
        self,
        screenplay,
        avatar_type: str,
        style: str = "anime"
    ) -> List[Dict[str, str]]:
        """
        Generate images for all scenes with consistent character appearance
        
        Args:
            screenplay: Screenplay object with scenes
            avatar_type: Character type to maintain consistency
            style: Art style (anime, cartoon, etc.)
        
        Returns:
            List of image paths/URLs for each scene
        """
        scene_images = []
        character_seed = self.character_seeds.get(
            avatar_type,
            f"{avatar_type} character"
        )
        
        for scene in screenplay.scenes:
            image_path = await self.generate_single_image(
                visual_description=scene.visual_description,
                character_seed=character_seed,
                style=style,
                scene_number=scene.scene_number
            )
            
            scene_images.append({
                "scene_number": scene.scene_number,
                "image_path": image_path,
                "description": scene.visual_description
            })
        
        return scene_images
    
    async def generate_single_image(
        self,
        visual_description: str,
        character_seed: str,
        style: str,
        scene_number: int
    ) -> str:
        """
        Generate a single scene image with consistent character
        
        Args:
            visual_description: Scene visual description
            character_seed: Character consistency token
            style: Art style
            scene_number: Scene identifier
        
        Returns:
            Path to generated image
        """
        # Construct the full prompt with character seed
        full_prompt = f"{style} art style, {character_seed}, {visual_description}, educational illustration, bright colors, child-friendly"
        
        # For now, return placeholder (implement API call when keys are available)
        if self.stability_key:
            return await self._generate_with_stability(full_prompt, scene_number)
        elif self.openai_key:
            return await self._generate_with_dalle(full_prompt, scene_number)
        else:
            return self._create_placeholder(scene_number)
    
    async def _generate_with_stability(self, prompt: str, scene_number: int) -> str:
        """Generate image using Stability AI API"""
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {self.stability_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                }
            ],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                # Save the image
                data = response.json()
                image_data = data["artifacts"][0]["base64"]
                
                # Decode and save
                import base64
                image_path = self.output_dir / f"scene_{scene_number}.png"
                with open(image_path, "wb") as f:
                    f.write(base64.b64decode(image_data))
                
                return str(image_path)
        
        except Exception as e:
            print(f"Stability AI error: {e}")
            return self._create_placeholder(scene_number)
    
    async def _generate_with_dalle(self, prompt: str, scene_number: int) -> str:
        """Generate image using DALL-E API"""
        try:
            import openai
            openai.api_key = self.openai_key
            
            response = await openai.Image.acreate(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            image_url = response['data'][0]['url']
            
            # Download and save the image
            async with httpx.AsyncClient() as client:
                img_response = await client.get(image_url)
                image_path = self.output_dir / f"scene_{scene_number}.png"
                
                with open(image_path, "wb") as f:
                    f.write(img_response.content)
            
            return str(image_path)
        
        except Exception as e:
            print(f"DALL-E error: {e}")
            return self._create_placeholder(scene_number)
    
    def _create_placeholder(self, scene_number: int) -> str:
        """Create placeholder image path when API is not available"""
        return f"/api/placeholder/scene_{scene_number}.png"
