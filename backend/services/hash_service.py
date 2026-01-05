"""
Hash Service for File Verification
Handles SHA-256 hash generation and duplicate detection across saved and generated stories
"""
import os
import hashlib
import json
from typing import Optional, Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class HashService:
    """Service for file hash generation and duplicate detection"""
    
    def __init__(self):
        self.saved_stories_dir = Path("saved_stories")
        self.generated_stories_dir = Path("generated_stories")
        self.hash_cache_file = Path("backend/hash_cache.json")
        self.hash_cache = self._load_hash_cache()
    
    def _load_hash_cache(self) -> Dict[str, Dict]:
        """Load hash cache from disk"""
        if self.hash_cache_file.exists():
            try:
                with open(self.hash_cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load hash cache: {e}")
        return {}
    
    def _save_hash_cache(self):
        """Save hash cache to disk"""
        try:
            self.hash_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.hash_cache_file, 'w') as f:
                json.dump(self.hash_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save hash cache: {e}")
    
    def generate_file_hash(self, file_path: str) -> str:
        """
        Generate SHA-256 hash for a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash as hex string
        """
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                # Read in chunks to handle large files
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error generating hash for {file_path}: {e}")
            raise
    
    def generate_bytes_hash(self, file_bytes: bytes) -> str:
        """
        Generate SHA-256 hash for file bytes
        
        Args:
            file_bytes: File content as bytes
            
        Returns:
            SHA-256 hash as hex string
        """
        return hashlib.sha256(file_bytes).hexdigest()
    
    def scan_directory_for_hash(self, target_hash: str, directory: Path) -> List[Dict]:
        """
        Scan a directory for files matching the target hash
        
        Args:
            target_hash: Hash to search for
            directory: Directory to scan
            
        Returns:
            List of matching file info dicts
        """
        matches = []
        
        if not directory.exists():
            return matches
        
        for story_dir in directory.iterdir():
            if not story_dir.is_dir():
                continue
            
            # Check metadata first if available
            metadata_file = story_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        cached_hash = metadata.get("file_hash")
                        if cached_hash == target_hash:
                            matches.append({
                                "story_id": story_dir.name,
                                "path": str(story_dir),
                                "source": "metadata",
                                "metadata": metadata
                            })
                            continue  # Found in metadata, no need to scan files
                except Exception:
                    pass
            
            # Scan all files in story directory
            for file_path in story_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.endswith('.json'):
                    try:
                        file_hash = self.generate_file_hash(str(file_path))
                        if file_hash == target_hash:
                            matches.append({
                                "story_id": story_dir.name,
                                "path": str(file_path),
                                "source": "file_scan",
                                "relative_path": file_path.relative_to(story_dir)
                            })
                    except Exception as e:
                        logger.warning(f"Could not hash {file_path}: {e}")
        
        return matches
    
    def find_duplicate(self, file_bytes: bytes, file_name: Optional[str] = None) -> Optional[Dict]:
        """
        Find if file content already exists in saved or generated stories
        
        Args:
            file_bytes: File content as bytes
            file_name: Optional filename for context
            
        Returns:
            Dict with duplicate info or None
        """
        file_hash = self.generate_bytes_hash(file_bytes)
        
        # Check cache first (for performance)
        cache_key = f"{file_hash}"
        if cache_key in self.hash_cache:
            cached = self.hash_cache[cache_key]
            # Check if cache is still valid (less than 24 hours old)
            import time
            if time.time() - cached.get("timestamp", 0) < 86400:
                logger.info(f"Hash found in cache: {file_hash[:16]}...")
                return cached.get("duplicate_info")
        
        # Scan both directories
        saved_matches = self.scan_directory_for_hash(file_hash, self.saved_stories_dir)
        generated_matches = self.scan_directory_for_hash(file_hash, self.generated_stories_dir)
        
        all_matches = saved_matches + generated_matches
        
        if all_matches:
            duplicate_info = {
                "hash": file_hash,
                "matches": all_matches,
                "saved_stories": saved_matches,
                "generated_stories": generated_matches
            }
            
            # Update cache
            self.hash_cache[cache_key] = {
                "timestamp": time.time(),
                "duplicate_info": duplicate_info
            }
            self._save_hash_cache()
            
            return duplicate_info
        
        return None
    
    def update_story_metadata_hash(self, story_id: str, file_hash: str, in_saved: bool = False):
        """
        Update story metadata with file hash
        
        Args:
            story_id: Story identifier
            file_hash: File hash to store
            in_saved: Whether story is in saved_stories
        """
        base_dir = self.saved_stories_dir if in_saved else self.generated_stories_dir
        metadata_path = base_dir / story_id / "metadata.json"
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                metadata["file_hash"] = file_hash
                
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Updated metadata with hash for story {story_id}")
            except Exception as e:
                logger.error(f"Failed to update metadata: {e}")
    
    def get_story_hash(self, story_id: str, in_saved: bool = False) -> Optional[str]:
        """
        Get file hash for a story from metadata
        
        Args:
            story_id: Story identifier
            in_saved: Whether story is in saved_stories
            
        Returns:
            File hash if found, None otherwise
        """
        base_dir = self.saved_stories_dir if in_saved else self.generated_stories_dir
        metadata_path = base_dir / story_id / "metadata.json"
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    return metadata.get("file_hash")
            except Exception:
                return None
        
        return None
    
    def clear_old_cache(self, max_age_hours: int = 24):
        """Remove cache entries older than specified hours"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        to_remove = []
        for key, data in self.hash_cache.items():
            if current_time - data.get("timestamp", 0) > max_age_seconds:
                to_remove.append(key)
        
        for key in to_remove:
            del self.hash_cache[key]
        
        if to_remove:
            logger.info(f"Cleared {len(to_remove)} old cache entries")
            self._save_hash_cache()

# Singleton instance
hash_service = HashService()
