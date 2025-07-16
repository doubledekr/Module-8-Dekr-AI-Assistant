import time
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiter for API requests based on user tiers"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        
        # Tier-based limits (messages per day)
        self.daily_limits = {
            1: 10,    # Freemium
            2: 50,    # Market Hours Pro
            3: 100,   # Tier 3
            4: 200,   # Tier 4
            5: 500,   # Tier 5
            6: 1000,  # Tier 6
            7: -1     # Tier 7 (unlimited)
        }
        
        # Rate limits (requests per minute)
        self.rate_limits = {
            1: 2,     # Freemium
            2: 5,     # Market Hours Pro
            3: 10,    # Tier 3
            4: 15,    # Tier 4
            5: 20,    # Tier 5
            6: 30,    # Tier 6
            7: 50     # Tier 7
        }
    
    def get_daily_limit_key(self, session_id: str) -> str:
        """Generate key for daily limit tracking"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        return f"daily_limit:{session_id}:{date_str}"
    
    def get_rate_limit_key(self, session_id: str) -> str:
        """Generate key for rate limit tracking"""
        return f"rate_limit:{session_id}"
    
    def check_daily_limit(self, session_id: str, user_tier: int) -> bool:
        """Check if user has exceeded daily message limit"""
        if not self.redis_client:
            return True  # Allow if Redis is not available
        
        daily_limit = self.daily_limits.get(user_tier, 10)
        
        # Unlimited for tier 7
        if daily_limit == -1:
            return True
        
        try:
            key = self.get_daily_limit_key(session_id)
            current_count = self.redis_client.get(key)
            current_count = int(current_count) if current_count else 0
            
            return current_count < daily_limit
        except Exception as e:
            self.logger.error(f"Error checking daily limit: {e}")
            return True  # Allow on error
    
    def check_rate_limit(self, session_id: str, user_tier: int) -> bool:
        """Check if user has exceeded rate limit"""
        if not self.redis_client:
            return True  # Allow if Redis is not available
        
        rate_limit = self.rate_limits.get(user_tier, 2)
        
        try:
            key = self.get_rate_limit_key(session_id)
            current_time = int(time.time())
            window_start = current_time - 60  # 1 minute window
            
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_count = self.redis_client.zcard(key)
            
            return current_count < rate_limit
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    def increment_usage(self, session_id: str) -> bool:
        """Increment usage counters after successful request"""
        if not self.redis_client:
            return True
        
        try:
            current_time = int(time.time())
            
            # Increment daily counter
            daily_key = self.get_daily_limit_key(session_id)
            self.redis_client.incr(daily_key)
            self.redis_client.expire(daily_key, 86400)  # 24 hours
            
            # Add to rate limit tracker
            rate_key = self.get_rate_limit_key(session_id)
            self.redis_client.zadd(rate_key, {str(current_time): current_time})
            self.redis_client.expire(rate_key, 60)  # 1 minute
            
            return True
        except Exception as e:
            self.logger.error(f"Error incrementing usage: {e}")
            return False
    
    def get_usage_stats(self, session_id: str) -> Dict[str, Any]:
        """Get current usage statistics for a session"""
        if not self.redis_client:
            return {}
        
        try:
            # Get daily usage
            daily_key = self.get_daily_limit_key(session_id)
            daily_count = self.redis_client.get(daily_key)
            daily_count = int(daily_count) if daily_count else 0
            
            # Get rate limit usage
            rate_key = self.get_rate_limit_key(session_id)
            current_time = int(time.time())
            window_start = current_time - 60
            
            # Clean old entries
            self.redis_client.zremrangebyscore(rate_key, 0, window_start)
            rate_count = self.redis_client.zcard(rate_key)
            
            return {
                'daily_messages_used': daily_count,
                'rate_limit_usage': rate_count,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting usage stats: {e}")
            return {}
    
    def reset_daily_limit(self, session_id: str) -> bool:
        """Reset daily limit for a session (admin function)"""
        if not self.redis_client:
            return True
        
        try:
            daily_key = self.get_daily_limit_key(session_id)
            self.redis_client.delete(daily_key)
            return True
        except Exception as e:
            self.logger.error(f"Error resetting daily limit: {e}")
            return False
    
    def get_remaining_messages(self, session_id: str, user_tier: int) -> int:
        """Get remaining messages for today"""
        if not self.redis_client:
            return 999  # Return high number if Redis unavailable
        
        daily_limit = self.daily_limits.get(user_tier, 10)
        
        # Unlimited for tier 7
        if daily_limit == -1:
            return 999
        
        try:
            daily_key = self.get_daily_limit_key(session_id)
            current_count = self.redis_client.get(daily_key)
            current_count = int(current_count) if current_count else 0
            
            return max(0, daily_limit - current_count)
        except Exception as e:
            self.logger.error(f"Error getting remaining messages: {e}")
            return 0
    
    def is_tier_upgrade_beneficial(self, session_id: str, current_tier: int) -> Dict[str, Any]:
        """Analyze if tier upgrade would be beneficial"""
        if not self.redis_client:
            return {'beneficial': False, 'reason': 'Cannot analyze without Redis'}
        
        try:
            # Get usage stats
            stats = self.get_usage_stats(session_id)
            daily_used = stats.get('daily_messages_used', 0)
            current_limit = self.daily_limits.get(current_tier, 10)
            
            # Check if user is close to limit
            usage_percentage = (daily_used / current_limit) * 100 if current_limit > 0 else 0
            
            if usage_percentage >= 80:
                next_tier = min(current_tier + 1, 7)
                next_limit = self.daily_limits.get(next_tier, current_limit)
                
                return {
                    'beneficial': True,
                    'current_usage': daily_used,
                    'current_limit': current_limit,
                    'usage_percentage': usage_percentage,
                    'recommended_tier': next_tier,
                    'next_tier_limit': next_limit,
                    'reason': f'You are using {usage_percentage:.1f}% of your daily limit'
                }
            
            return {
                'beneficial': False,
                'current_usage': daily_used,
                'current_limit': current_limit,
                'usage_percentage': usage_percentage,
                'reason': 'Your current tier seems sufficient for your usage pattern'
            }
        except Exception as e:
            self.logger.error(f"Error analyzing tier upgrade: {e}")
            return {'beneficial': False, 'reason': 'Error analyzing usage'}
