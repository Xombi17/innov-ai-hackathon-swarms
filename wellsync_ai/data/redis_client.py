"""
Redis client setup and management for WellSync AI system.

Handles Redis connections for real-time state sharing
and working memory across agents.
"""

import json
import redis
from typing import Dict, Any, Optional, List
from wellsync_ai.utils.config import get_config

config = get_config()


class RedisManager:
    """Manages Redis operations with in-memory fallback."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or config.redis_url
        self._client = None
        self._use_redis = True
        self._in_memory_store = {}
        
        # Test initial connection
        try:
            client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            client.ping()
        except Exception:
            print("Redis not available, using in-memory fallback")
            self._use_redis = False
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client with lazy initialization."""
        if not self._use_redis:
            return None
            
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            except Exception:
                self._use_redis = False
                return None
        return self._client
    
    def test_connection(self) -> bool:
        """Test Redis connection."""
        if not self._use_redis:
            return False
        try:
            self.client.ping()
            return True
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self._use_redis = False
            return False
    
    def set_shared_state(self, key: str, data: Dict[str, Any], 
                        ttl: Optional[int] = None) -> bool:
        """Set shared state data with optional TTL."""
        if self._use_redis:
            try:
                ttl = ttl or config.redis_memory_ttl_seconds
                self.client.setex(
                    f"shared_state:{key}",
                    ttl,
                    json.dumps(data)
                )
                return True
            except Exception as e:
                print(f"Redis set failed, falling back: {e}")
                self._use_redis = False
        
        # Fallback
        self._in_memory_store[f"shared_state:{key}"] = json.dumps(data)
        return True
    
    def get_shared_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Get shared state data."""
        if self._use_redis:
            try:
                data = self.client.get(f"shared_state:{key}")
                return json.loads(data) if data else None
            except Exception as e:
                print(f"Redis get failed, falling back: {e}")
                self._use_redis = False
        
        # Fallback
        data = self._in_memory_store.get(f"shared_state:{key}")
        return json.loads(data) if data else None
    
    def set_agent_working_memory(self, agent_name: str, data: Dict[str, Any], 
                                ttl: Optional[int] = None) -> bool:
        """Set agent working memory."""
        if self._use_redis:
            try:
                ttl = ttl or config.redis_memory_ttl_seconds
                self.client.setex(
                    f"agent_memory:{agent_name}",
                    ttl,
                    json.dumps(data)
                )
                return True
            except Exception as e:
                print(f"Redis set failed, falling back: {e}")
                self._use_redis = False
        
        # Fallback
        self._in_memory_store[f"agent_memory:{agent_name}"] = json.dumps(data)
        return True
    
    def get_agent_working_memory(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent working memory."""
        if self._use_redis:
            try:
                data = self.client.get(f"agent_memory:{agent_name}")
                return json.loads(data) if data else None
            except Exception as e:
                print(f"Redis get failed, falling back: {e}")
                self._use_redis = False
        
        # Fallback
        data = self._in_memory_store.get(f"agent_memory:{agent_name}")
        return json.loads(data) if data else None
    
    def publish_agent_message(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish message to agent communication channel."""
        if self._use_redis:
            try:
                self.client.publish(channel, json.dumps(message))
                return True
            except Exception as e:
                print(f"Redis publish failed: {e}")
                self._use_redis = False
        return False
    
    def subscribe_to_channel(self, channel: str):
        """Subscribe to agent communication channel."""
        if self._use_redis:
            try:
                pubsub = self.client.pubsub()
                pubsub.subscribe(channel)
                return pubsub
            except Exception as e:
                print(f"Redis subscribe failed: {e}")
                self._use_redis = False
        return None
    
    def set_workflow_status(self, workflow_id: str, status: str, 
                           data: Optional[Dict[str, Any]] = None) -> bool:
        """Set workflow execution status."""
        status_data = {
            'status': status,
            'timestamp': json.dumps(data) if data else None,
            'data': data
        }
        
        if self._use_redis:
            try:
                self.client.setex(
                    f"workflow:{workflow_id}",
                    config.workflow_timeout_seconds,
                    json.dumps(status_data)
                )
                return True
            except Exception as e:
                print(f"Redis set failed, falling back: {e}")
                self._use_redis = False
        
        # Fallback
        self._in_memory_store[f"workflow:{workflow_id}"] = json.dumps(status_data)
        return True
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status."""
        if self._use_redis:
            try:
                data = self.client.get(f"workflow:{workflow_id}")
                return json.loads(data) if data else None
            except Exception as e:
                print(f"Redis get failed, falling back: {e}")
                self._use_redis = False
        
        # Fallback
        data = self._in_memory_store.get(f"workflow:{workflow_id}")
        return json.loads(data) if data else None
    
    def clear_expired_data(self) -> int:
        """Clear expired data."""
        if self._use_redis:
            try:
                # Get all keys with our prefixes
                patterns = [
                    "shared_state:*",
                    "agent_memory:*", 
                    "workflow:*"
                ]
                
                cleared_count = 0
                for pattern in patterns:
                    keys = self.client.keys(pattern)
                    for key in keys:
                        ttl = self.client.ttl(key)
                        if ttl == -1:  # No expiration set
                            self.client.expire(key, config.redis_memory_ttl_seconds)
                        elif ttl == -2:  # Key doesn't exist
                            cleared_count += 1
                return cleared_count
            except Exception as e:
                print(f"Failed to clear expired data from Redis: {e}")
                self._use_redis = False
        return 0 # Simplified cleanup for fallback
    
    def health_check(self) -> bool:
        """Perform health check."""
        return self._use_redis or isinstance(self._in_memory_store, dict)
    
    def get_health_info(self) -> Dict[str, Any]:
        """Get detailed health information."""
        if self._use_redis:
            try:
                info = self.client.info()
                return {
                    'connected': True,
                    'mode': 'redis',
                    'redis_version': info.get('redis_version'),
                    'used_memory': info.get('used_memory_human')
                }
            except Exception:
                self._use_redis = False
        
        return {
            'connected': True,
            'mode': 'in-memory_fallback',
            'items_count': len(self._in_memory_store)
        }


# Global Redis manager instance
redis_manager = RedisManager()


def get_redis_manager() -> RedisManager:
    """Get the global Redis manager instance."""
    return redis_manager


def test_redis_connection() -> bool:
    """Test Redis connection."""
    return redis_manager.test_connection()