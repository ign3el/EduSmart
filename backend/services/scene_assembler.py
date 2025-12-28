"""
Scene Assembler Service
Combines generated images and audio into a synchronized timeline
"""

import json
from typing import List, Dict
from pathlib import Path


class SceneAssembler:
    """Assembles screenplay, images, and audio into a playable timeline"""
    
    def __init__(self):
        self.output_dir = Path("outputs/stories")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def assemble(
        self,
        screenplay,
        images: List[Dict],
        audio: List[Dict],
        story_id: str
    ) -> Dict:
        """
        Create a timeline structure combining all assets
        
        Args:
            screenplay: Screenplay with scenes
            images: List of generated scene images
            audio: List of generated voiceovers
            story_id: Unique story identifier
        
        Returns:
            Timeline dictionary with all synchronized assets
        """
        timeline = {
            "story_id": story_id,
            "total_scenes": len(screenplay.scenes),
            "scenes": []
        }
        
        # Combine all assets by scene number
        for scene in screenplay.scenes:
            scene_data = {
                "scene_number": scene.scene_number,
                "visual_description": scene.visual_description,
                "narration": scene.narration,
                "learning_point": scene.learning_point,
                "image": self._find_asset(images, scene.scene_number, "image_path"),
                "audio": self._find_asset(audio, scene.scene_number, "audio_path"),
                "duration": self._find_asset(audio, scene.scene_number, "duration", default=5.0)
            }
            
            timeline["scenes"].append(scene_data)
        
        # Calculate total duration
        timeline["total_duration"] = sum(
            scene["duration"] for scene in timeline["scenes"]
        )
        
        # Save timeline to JSON file
        timeline_path = self.output_dir / f"{story_id}.json"
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
        
        timeline["timeline_path"] = str(timeline_path)
        
        return timeline
    
    def _find_asset(
        self,
        asset_list: List[Dict],
        scene_number: int,
        key: str,
        default=None
    ):
        """
        Find an asset from the list by scene number
        
        Args:
            asset_list: List of asset dictionaries
            scene_number: Scene to find
            key: Key to extract from asset
            default: Default value if not found
        
        Returns:
            Asset value or default
        """
        for asset in asset_list:
            if asset.get("scene_number") == scene_number:
                return asset.get(key, default)
        return default
    
    async def get_timeline(self, story_id: str) -> Dict:
        """
        Retrieve a saved timeline
        
        Args:
            story_id: Story identifier
        
        Returns:
            Timeline dictionary
        """
        timeline_path = self.output_dir / f"{story_id}.json"
        
        if timeline_path.exists():
            with open(timeline_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        return None
