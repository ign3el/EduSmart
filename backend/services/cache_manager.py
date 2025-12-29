"""
Cache Manager Service
Handles caching of generated content (screenplay, images, audio) using Redis
"""
import hashlib
import json
import logging
from typing import Optional, Dict

import redis.asyncio as aioredis
from redis.exceptions import RedisError
from config import Config

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of AI-generated content using redis.asyncio."""

    _redis: Optional[aioredis.Redis] = None

    def __init__(self):
        self.redis_url = Config.REDIS_URL
        self.cache_ttl = Config.CACHE_TTL
        self.use_cache = Config.USE_CACHE

    async def _get_redis(self) -> Optional[aioredis.Redis]:
        """Initializes and returns the redis connection."""
        if not self.use_cache:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
                logger.info("Successfully connected to Redis.")
            except (aioredis.ConnectionError, OSError) as e:
                logger.error(f"Redis connection failed: {e}. Continuing without cache.")
                self._redis = None
        return self._redis

    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Generates a consistent cache key from parameters."""
        sorted_items = sorted(kwargs.items())
        param_str = json.dumps(sorted_items)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"{prefix}:{param_hash}"

    async def get(self, prefix: str, **kwargs) -> Optional[str]:
        """Retrieves cached content."""
        redis = await self._get_redis()
        if not redis:
            return None

        key = self._generate_key(prefix, **kwargs)
        try:
            value = await redis.get(key)
            if value:
                logger.info(f"Cache hit: {key}")
                return value
            logger.info(f"Cache miss: {key}")
            return None
        except (RedisError, OSError) as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None

    async def set(self, prefix: str, value: str, **kwargs) -> bool:
        """Stores content in the cache with a TTL."""
        redis = await self._get_redis()
        if not redis:
            return False

        key = self._generate_key(prefix, **kwargs)
        try:
            await redis.setex(key, self.cache_ttl, value)
            logger.info(f"Cached: {key}")
            return True
        except (RedisError, OSError) as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False

    async def get_json(self, prefix: str, **kwargs) -> Optional[Dict]:
        """Gets a cached JSON object."""
        cached_str = await self.get(prefix, **kwargs)
        if cached_str:
            try:
                return json.loads(cached_str)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode cached JSON for prefix {prefix}", exc_info=True)
                return None
        return None

    async def set_json(self, prefix: str, value: Dict, **kwargs) -> bool:
        """Stores a JSON object in the cache."""
        try:
            json_value = json.dumps(value)
            return await self.set(prefix, json_value, **kwargs)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize JSON for prefix {prefix}: {e}")
            return False

    async def clear_prefix(self, prefix: str) -> int:
        """Clears all cache entries for a given prefix."""
        redis = await self._get_redis()
        if not redis:
            return 0

        pattern = f"{prefix}:*"
        try:
            keys = await redis.keys(pattern)
            if keys:
                deleted_count = await redis.delete(*keys)
                logger.info(f"Cleared {deleted_count} keys for prefix '{prefix}'")
                return deleted_count
            return 0
        except (RedisError, OSError) as e:
            logger.error(f"Cache clear error for prefix {prefix}: {e}")
            return 0

    async def health_check(self) -> bool:
        """Checks if the cache is available and responsive."""
        redis = await self._get_redis()
        if not redis:
            return False
        try:
            return await redis.ping()
        except (RedisError, OSError):
            return False