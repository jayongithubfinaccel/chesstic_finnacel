"""
Input validation utilities.
"""
import re
from datetime import datetime
from typing import Optional


def validate_username(username: Optional[str]) -> bool:
    """
    Validate Chess.com username.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not username:
        return False
    
    # Chess.com usernames are alphanumeric with underscores and hyphens
    pattern = r'^[a-zA-Z0-9_-]{3,25}$'
    return bool(re.match(pattern, username))


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> bool:
    """
    Validate date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        True if valid, False otherwise
    """
    if not start_date or not end_date:
        return False
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Ensure start is before end
        if start > end:
            return False
        
        # Ensure dates are not in the future
        if end > datetime.now():
            return False
        
        return True
        
    except ValueError:
        return False
