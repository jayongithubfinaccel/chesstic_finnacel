"""
Timezone conversion utilities for accurate time-based analysis.
"""
from datetime import datetime
from typing import Optional
import pytz


def convert_utc_to_timezone(utc_timestamp: int, timezone_str: str) -> datetime:
    """
    Convert UTC timestamp to specified timezone.
    
    Args:
        utc_timestamp: Unix timestamp in UTC
        timezone_str: Timezone string (e.g., 'America/New_York')
        
    Returns:
        Datetime object in specified timezone
    """
    try:
        utc_time = datetime.utcfromtimestamp(utc_timestamp)
        utc_time = pytz.utc.localize(utc_time)
        target_tz = pytz.timezone(timezone_str)
        return utc_time.astimezone(target_tz)
    except Exception:
        # Fallback to UTC if conversion fails
        return datetime.utcfromtimestamp(utc_timestamp)


def get_time_of_day_category(dt: datetime) -> str:
    """
    Categorize time into morning, afternoon, or night.
    
    Morning: 6:00 AM - 2:00 PM
    Afternoon: 2:00 PM - 10:00 PM
    Night: 10:00 PM - 6:00 AM
    
    Args:
        dt: Datetime object in user's timezone
        
    Returns:
        Category: 'morning', 'afternoon', or 'night'
    """
    hour = dt.hour
    
    if 6 <= hour < 14:
        return 'morning'
    elif 14 <= hour < 22:
        return 'afternoon'
    else:
        return 'night'


def validate_timezone(timezone_str: Optional[str]) -> bool:
    """
    Validate timezone string.
    
    Args:
        timezone_str: Timezone string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not timezone_str:
        return False
    
    try:
        pytz.timezone(timezone_str)
        return True
    except pytz.exceptions.UnknownTimeZoneError:
        return False


def get_date_string(dt: datetime) -> str:
    """
    Get date string in YYYY-MM-DD format.
    
    Args:
        dt: Datetime object
        
    Returns:
        Date string
    """
    return dt.strftime('%Y-%m-%d')
