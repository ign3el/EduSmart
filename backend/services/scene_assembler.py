"""
Scene Assembler Service
Combines generated images and audio into a synchronized timeline.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SceneAssembler:
    """Assembles screenplay, images, and audio into a playable timeline."""

    def __init__(self):
        self.output_dir = Path("outputs/stories")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _find_asset(self, asset_list: List[Dict], scene_number: int, key: str, default: Any = None) -> Any:
        """Finds an asset from a list by scene number."""
        for asset in asset_list:
            if asset.get("scene_number") == scene_number:
                return asset.get(key, default)
        return default

    def _save_timeline_sync(self, timeline: Dict, path: Path):
        """Saves the timeline to a JSON file (synchronous)."""
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(timeline, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully saved timeline to {path}")
        except IOError as e:
            logger.error(f"Failed to save timeline to {path}: {e}", exc_info=True)
            # Decide if re-raising is necessary or if logging is sufficient.
            # For this case, we'll let the calling async method handle the error.
            raise

    async def assemble(self, screenplay, images: List[Dict], audio: List[Dict], story_id: str) -> Dict:
        """
        Creates a timeline structure combining all assets and saves it asynchronously.
        """
        scenes_data = []
        for scene in screenplay.scenes:
            scene_data = {
                "scene_number": scene.scene_number,
                "visual_description": scene.visual_description,
                "narration": scene.narration,
                "learning_point": scene.learning_point,
                "image": self._find_asset(images, scene.scene_number, "image_path"),
                "audio": self._find_asset(audio, scene.scene_number, "audio_path"),
                "duration": self._find_asset(audio, scene.scene_number, "duration", default=5.0),
            }
            scenes_data.append(scene_data)

        timeline = {
            "story_id": story_id,
            "total_scenes": len(scenes_data),
            "total_duration": sum(scene["duration"] for scene in scenes_data),
            "scenes": scenes_data,
        }

        timeline_path = self.output_dir / f"{story_id}.json"
        
        try:
            await asyncio.to_thread(self._save_timeline_sync, timeline, timeline_path)
            timeline["timeline_path"] = str(timeline_path)
        except Exception as e:
            # The error is already logged in the sync method.
            # We can add more context here if needed.
            timeline["timeline_path"] = None # Indicate failure
        
        return timeline

    def _get_timeline_sync(self, path: Path) -> Optional[Dict]:
        """Reads a timeline from a JSON file (synchronous)."""
        if not path.exists():
            logger.warning(f"Timeline file not found at {path}")
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to read or parse timeline from {path}: {e}", exc_info=True)
            return None

    async def get_timeline(self, story_id: str) -> Optional[Dict]:
        """
        Retrieves a saved timeline asynchronously.
        """
        timeline_path = self.output_dir / f"{story_id}.json"
        return await asyncio.to_thread(self._get_timeline_sync, timeline_path)