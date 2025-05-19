"""
Custom caching functionality for the scheduler application.
"""
from django.core.cache import cache
from django.conf import settings
import hashlib
import json

class SchedulerCache:
    """
    Handles caching operations for the scheduler application to improve performance.
    """
    # Cache time for schedule results (4 hours)
    SCHEDULE_CACHE_TIME = 60 * 60 * 4
    
    # Cache time for student and course data (12 hours)
    DATA_CACHE_TIME = 60 * 60 * 12
    
    @staticmethod
    def generate_key(prefix, **kwargs):
        """
        Generate a cache key based on the prefix and kwargs.
        
        Args:
            prefix (str): The prefix for the cache key
            kwargs: Any parameters to include in the key generation
            
        Returns:
            str: A unique cache key
        """
        # Convert kwargs to sorted JSON for consistent key generation
        sorted_items = sorted(kwargs.items())
        key_data = json.dumps(sorted_items)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    @staticmethod
    def get_schedule_cache(school_id, **params):
        """
        Get cached schedule results.
        
        Args:
            school_id (int): The school ID
            params: Parameters used for scheduling
            
        Returns:
            dict: Cached schedule results or None if not found
        """
        cache_key = SchedulerCache.generate_key(f"schedule:{school_id}", **params)
        return cache.get(cache_key)
    
    @staticmethod
    def set_schedule_cache(school_id, schedule_results, **params):
        """
        Cache schedule results.
        
        Args:
            school_id (int): The school ID
            schedule_results (dict): The schedule results to cache
            params: Parameters used for scheduling
        """
        cache_key = SchedulerCache.generate_key(f"schedule:{school_id}", **params)
        cache.set(cache_key, schedule_results, SchedulerCache.SCHEDULE_CACHE_TIME)
    
    @staticmethod
    def invalidate_schedule_cache(school_id):
        """
        Invalidate all schedule caches for a school when data changes.
        
        Args:
            school_id (int): The school ID
        """
        # Since we can't easily list all keys with a prefix in some cache backends,
        # we'll use a special marker key to track when data was last modified
        cache_invalidation_key = f"schedule_invalidation:{school_id}"
        cache.set(cache_invalidation_key, True)
    
    @staticmethod
    def clear_all_caches():
        """Clear all caches in the system."""
        cache.clear()
