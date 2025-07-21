import json
from typing import Dict, List, Optional
from loguru import logger
from .connection_manager import ConnectionManager

class RedisManager:
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self._setup_redis()
    
    def _setup_redis(self):
        try:
            self.redis_client = self.connection_manager.get_redis_connection()
            self.redis_client.ping()
            logger.info("Redis client ready")
        except Exception as e:
            logger.error(f"Failed to setup Redis client: {e}")
            raise
    
    def cache_user_profile(self, user_id: str, profile: Dict, ttl: int = 3600):
        """Cache user profile"""
        try:
            key = f"user_profile:{user_id}"
            self.redis_client.setex(key, ttl, json.dumps(profile))
            logger.debug(f"Cached user profile for {user_id}")
        except Exception as e:
            logger.error(f"Failed to cache user profile: {e}")
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get cached user profile"""
        try:
            key = f"user_profile:{user_id}"
            profile_str = await self.redis_client.get(key)
            if profile_str:
                return json.loads(profile_str)
            return None
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    def cache_recommendations(self, user_id: str, recommendations: List[str], ttl: int = 1800):
        """Cache user recommendations"""
        try:
            key = f"recommendations:{user_id}"
            self.redis_client.setex(key, ttl, json.dumps(recommendations))
            logger.debug(f"Cached recommendations for {user_id}")
        except Exception as e:
            logger.error(f"Failed to cache recommendations: {e}")
    
    async def get_recommendations(self, user_id: str) -> Optional[List[str]]:
        """Get cached recommendations"""
        try:
            key = f"recommendations:{user_id}"
            recs_str = await self.redis_client.get(key)
            if recs_str:
                return json.loads(recs_str)
            return None
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return None
    
    def update_user_interaction_count(self, user_id: str, interaction_type: str):
        """Update user interaction count"""
        try:
            key = f"user_interactions:{user_id}:{interaction_type}"
            self.redis_client.incr(key)
            # Set expiration for 24 hours
            self.redis_client.expire(key, 86400)
        except Exception as e:
            logger.error(f"Failed to update interaction count: {e}")
    
    async def get_trending_items(self, limit: int = 10) -> List[str]:
        """Get trending items based on interaction counts"""
        try:
            trending = await self.redis_client.zrevrange("trending_items", 0, limit-1)
            return list(trending)
        except Exception as e:
            logger.error(f"Failed to get trending items: {e}")
            return []
    
    def update_item_popularity(self, item_id: str, score: float = 1.0):
        """Update item popularity score"""
        try:
            self.redis_client.zincrby("trending_items", score, item_id)
            # Keep only top 1000 items
            self.redis_client.zremrangebyrank("trending_items", 0, -1001)
        except Exception as e:
            logger.error(f"Failed to update item popularity: {e}")
