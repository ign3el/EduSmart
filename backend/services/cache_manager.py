"""
Cache Manager Service
Handles caching of generated content (screenplay, images, audio) using Redis
"""

import hashlib
import json
import asyncio
from typing import Optional, Dict, Any
import os

try:
    import redis
    import aioredis
except ImportError:
    redis = None
    aioredis = None


class CacheManager:
    """Manages caching of AI-generated content"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.cache_ttl = int(os.getenv("CACHE_TTL", 86400))  # 24 hours default
        self.use_cache = os.getenv("USE_CACHE", "true").lower() == "true"
        self.redis = None
        
        if self.use_cache and redis is not None:
            try:
                self.redis = redis.from_url(self.redis_url, decode_responses=True)
                self.redis.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}. Continuing without cache.")
                self.redis = None
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a cache key from parameters
        
        Args:
            prefix: Cache key prefix (e.g., 'screenplay', 'image', 'audio')
            **kwargs: Parameters to hash (text, grade_level, avatar_type, etc.)
        
        Returns:
            Cache key string
        """
        # Sort kwargs to ensure consistent hashing
        sorted_items = sorted(kwargs.items())
        param_str = json.dumps(sorted_items)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        return f"{prefix}:{param_hash}"
    
    async def get(self, prefix: str, **kwargs) -> Optional[str]:
        """
        Retrieve cached content
        
        Args:
            prefix: Cache key prefix
            **kwargs: Parameters used to generate key
        
        Returns:
            Cached content or None
        """
        if not self.use_cache or self.redis is None:
            return None
        
        try:
            key = self._generate_key(prefix, **kwargs)
            value = self.redis.get(key)
            
            if value:
                print(f"Cache hit: {key}")
                return value
            
            return None
        
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, prefix: str, value: str, **kwargs) -> bool:
        """
        Store content in cache
        
        Args:
            prefix: Cache key prefix
            value: Content to cache
            **kwargs: Parameters used to generate key
        
        Returns:
            Success status
        """
        if not self.use_cache or self.redis is None:
            return False
        
        try:
            key = self._generate_key(prefix, **kwargs)
            self.redis.setex(key, self.cache_ttl, value)
            print(f"Cached: {key}")
            return True
        
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def get_json(self, prefix: str, **kwargs) -> Optional[Dict]:
        """Get cached JSON object"""
        cached = await self.get(prefix, **kwargs)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(self, prefix: str, value: Dict, **kwargs) -> bool:
        """Store JSON object in cache"""
        return await self.set(prefix, json.dumps(value), **kwargs)
    
    async def clear_prefix(self, prefix: str) -> int:
        """
        Clear all cache entries for a prefix
        
        Args:
            prefix: Cache key prefix
        
        Returns:
            Number of keys deleted
        """
        if not self.use_cache or self.redis is None:
            return 0
        
        try:
            pattern = f"{prefix}:*"
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0
    
    async def health_check(self) -> bool:
        """Check if cache is available"""
        if not self.use_cache:
            return False
        
        if self.redis is None:
            return False
        
        try:
            return self.redis.ping()
        except Exception:
            return False
