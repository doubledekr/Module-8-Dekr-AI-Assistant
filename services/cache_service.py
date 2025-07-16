import json
import logging
from typing import Any, Optional
from datetime import timedelta

class CacheService:
    """Service for caching responses and data"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        self.default_timeout = 300  # 5 minutes
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.redis_client:
            return None
        
        try:
            cached_value = self.redis_client.get(key)
            if cached_value:
                return json.loads(cached_value)
            return None
        except Exception as e:
            self.logger.error(f"Error getting cached value for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: int = None) -> bool:
        """Set cached value"""
        if not self.redis_client:
            return False
        
        try:
            timeout = timeout or self.default_timeout
            serialized_value = json.dumps(value, default=str)
            self.redis_client.setex(key, timeout, serialized_value)
            return True
        except Exception as e:
            self.logger.error(f"Error setting cached value for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cached value"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting cached value for key {key}: {e}")
            return False
    
    def get_conversation_cache_key(self, session_id: str, message_hash: str) -> str:
        """Generate cache key for conversation responses"""
        return f"conversation:{session_id}:{message_hash}"
    
    def get_market_data_cache_key(self, symbol: str) -> str:
        """Generate cache key for market data"""
        return f"market_data:{symbol}"
    
    def get_news_cache_key(self, symbols: str = "general") -> str:
        """Generate cache key for news data"""
        return f"news:{symbols}"
    
    def cache_response(self, session_id: str, user_message: str, ai_response: str, timeout: int = None) -> bool:
        """Cache AI response for similar queries"""
        try:
            # Create a simple hash of the user message for caching
            import hashlib
            message_hash = hashlib.md5(user_message.lower().encode()).hexdigest()
            key = self.get_conversation_cache_key(session_id, message_hash)
            
            cache_data = {
                "user_message": user_message,
                "ai_response": ai_response,
                "timestamp": str(timedelta(seconds=timeout or self.default_timeout))
            }
            
            return self.set(key, cache_data, timeout)
        except Exception as e:
            self.logger.error(f"Error caching response: {e}")
            return False
    
    def get_cached_response(self, session_id: str, user_message: str) -> Optional[str]:
        """Get cached AI response for similar queries"""
        try:
            import hashlib
            message_hash = hashlib.md5(user_message.lower().encode()).hexdigest()
            key = self.get_conversation_cache_key(session_id, message_hash)
            
            cached_data = self.get(key)
            if cached_data:
                return cached_data.get("ai_response")
            return None
        except Exception as e:
            self.logger.error(f"Error getting cached response: {e}")
            return None
    
    def cache_market_data(self, symbol: str, data: Any, timeout: int = 60) -> bool:
        """Cache market data with shorter timeout"""
        key = self.get_market_data_cache_key(symbol)
        return self.set(key, data, timeout)
    
    def get_cached_market_data(self, symbol: str) -> Optional[Any]:
        """Get cached market data"""
        key = self.get_market_data_cache_key(symbol)
        return self.get(key)
    
    def clear_session_cache(self, session_id: str) -> bool:
        """Clear all cached data for a session"""
        if not self.redis_client:
            return False
        
        try:
            pattern = f"conversation:{session_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            self.logger.error(f"Error clearing session cache: {e}")
            return False
