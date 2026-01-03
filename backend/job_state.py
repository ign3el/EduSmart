"""
Job state manager using SQLite for scene-level tracking.
Isolated per application, no Redis required.
"""
import sqlite3
import json
import threading
from typing import Optional, Dict, List
from datetime import datetime
from contextlib import contextmanager

class JobStateManager:
    def __init__(self, db_path: str = "job_state.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        """Thread-safe connection management."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        try:
            yield self._local.conn
        except Exception:
            self._local.conn.rollback()
            raise
        else:
            self._local.conn.commit()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stories (
                    story_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    title TEXT,
                    grade_level TEXT,
                    total_scenes INTEGER,
                    completed_scenes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scenes (
                    scene_id TEXT PRIMARY KEY,
                    story_id TEXT NOT NULL,
                    scene_index INTEGER NOT NULL,
                    text TEXT,
                    image_status TEXT DEFAULT 'pending',
                    audio_status TEXT DEFAULT 'pending',
                    image_url TEXT,
                    audio_url TEXT,
                    character_prompt TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (story_id) REFERENCES stories(story_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_scenes_story 
                ON scenes(story_id, scene_index)
            """)
    
    def initialize_story(self, story_id: str, grade_level: str):
        """Create a preliminary story job record."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO stories (story_id, status, title, grade_level, total_scenes, completed_scenes)
                VALUES (?, 'initializing', 'Initializing story...', ?, 0, 0)
            """, (story_id, grade_level))

    def update_story_metadata(self, story_id: str, title: str, total_scenes: int):
        """Update story metadata after initial AI processing."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE stories
                SET status = 'processing', title = ?, total_scenes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE story_id = ?
            """, (title, total_scenes, story_id))
    
    def create_scene(self, story_id: str, scene_index: int, text: str, character_prompt: Optional[str] = None):
        """Create a new scene for tracking."""
        scene_id = f"{story_id}_scene_{scene_index}"
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO scenes (scene_id, story_id, scene_index, text, character_prompt)
                VALUES (?, ?, ?, ?, ?)
            """, (scene_id, story_id, scene_index, text, character_prompt))
        return scene_id
    
    def update_scene_image(self, scene_id: str, status: str, image_url: Optional[str] = None):
        """Update scene image status."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE scenes 
                SET image_status = ?, image_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE scene_id = ?
            """, (status, image_url, scene_id))
            self._check_story_completion(scene_id)
    
    def update_scene_audio(self, scene_id: str, status: str, audio_url: Optional[str] = None):
        """Update scene audio status."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE scenes 
                SET audio_status = ?, audio_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE scene_id = ?
            """, (status, audio_url, scene_id))
            self._check_story_completion(scene_id)
    
    def _check_story_completion(self, scene_id: str):
        """Check if all scenes are complete and update story status."""
        with self._get_conn() as conn:
            # Get story_id from scene
            row = conn.execute("SELECT story_id FROM scenes WHERE scene_id = ?", (scene_id,)).fetchone()
            if not row:
                return
            
            story_id = row['story_id']
            
            # Count completed scenes
            result = conn.execute("""
                SELECT COUNT(*) as completed
                FROM scenes
                WHERE story_id = ? 
                AND image_status = 'completed' 
                AND audio_status = 'completed'
            """, (story_id,)).fetchone()
            
            completed = result['completed']
            
            # Get total scenes
            story = conn.execute("SELECT total_scenes FROM stories WHERE story_id = ?", (story_id,)).fetchone()
            total = story['total_scenes']
            
            # Update story
            conn.execute("""
                UPDATE stories
                SET completed_scenes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE story_id = ?
            """, (completed, story_id))
            
            # Mark as completed if all done
            if completed == total:
                conn.execute("""
                    UPDATE stories
                    SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                    WHERE story_id = ?
                """, (story_id,))
    
    def get_story_status(self, story_id: str) -> Optional[Dict]:
        """Get overall story status."""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM stories WHERE story_id = ?
            """, (story_id,)).fetchone()
            
            if not row:
                return None
            
            return dict(row)
    
    def get_scene(self, scene_id: str) -> Optional[Dict]:
        """Get specific scene data."""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM scenes WHERE scene_id = ?
            """, (scene_id,)).fetchone()
            
            if not row:
                return None
            
            return dict(row)
    
    def get_all_scenes(self, story_id: str) -> List[Dict]:
        """Get all scenes for a story."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM scenes 
                WHERE story_id = ?
                ORDER BY scene_index
            """, (story_id,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def mark_story_failed(self, story_id: str, error: Optional[str] = None):
        """Mark story as failed."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE stories
                SET status = 'failed', updated_at = CURRENT_TIMESTAMP
                WHERE story_id = ?
            """, (story_id,))

# Global instance
job_manager = JobStateManager()
