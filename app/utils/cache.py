"""
Simple caching decorator for API responses.
"""
from functools import wraps
from typing import Callable
import time


# Simple in-memory cache
_cache = {}
_cache_timestamps = {}


def cache_response(ttl: int = 300) -> Callable:
    """
    Cache decorator for functions.
    
    Args:
        ttl: Time to live in seconds (default 5 minutes)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if cached and not expired
            if cache_key in _cache:
                timestamp = _cache_timestamps.get(cache_key, 0)
                if time.time() - timestamp < ttl:
                    return _cache[cache_key]
            
            # Call function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = time.time()
            
            return result
        
        return wrapper
    return decorator


def clear_cache():
    """Clear all cached data."""
    _cache.clear()
    _cache_timestamps.clear()
