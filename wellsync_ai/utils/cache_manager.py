import hashlib
import json
import logging
from typing import Any, Optional, Dict
import redis
import os
from datetime import timedelta

logger = logging.getLogger(__name__)

class CacheManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self.default_ttl = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
        
        self.redis_client = None
        self.local_cache = {}
        
        try:
            if self.enabled:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("CacheManager: Connected to Redis")
        except Exception as e:
            logger.warning(f"CacheManager: Failed to connect to Redis, using in-memory fallback. Error: {e}")
            self.redis_client = None

    def generate_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate a consistent cache key based on data content."""
        try:
            # Sort keys to ensure consistent ordering
            serialized = json.dumps(data, sort_keys=True)
            hash_val = hashlib.sha256(serialized.encode()).hexdigest()
            return f"{prefix}:{hash_val}"
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            return f"{prefix}:{hashlib.sha256(str(data).encode()).hexdigest()}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve item from cache."""
        if not self.enabled:
            return None
            
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # Simple in-memory fallback (no generic TTL enforcement for simplicity in fallback)
                return self.local_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
            
        return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Store item in cache with TTL."""
        if not self.enabled:
            return False
            
        ttl = ttl or self.default_ttl
        
        try:
            serialized_value = json.dumps(value)
            if self.redis_client:
                self.redis_client.setex(key, timedelta(seconds=ttl), serialized_value)
            else:
                self.local_cache[key] = value
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching a pattern."""
        if not self.enabled:
            return

        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Simple prefix matching for local cache
                keys_to_delete = [k for k in self.local_cache.keys() if k.startswith(pattern.replace('*', ''))]
                for k in keys_to_delete:
                    del self.local_cache[k]
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

def get_cache_manager():
    return CacheManager()
