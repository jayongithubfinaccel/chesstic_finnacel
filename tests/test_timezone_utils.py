"""
Unit tests for timezone utilities module.
"""
import pytest
from datetime import datetime
import pytz
from app.utils.timezone_utils import (
    convert_utc_to_timezone,
    get_time_of_day_category,
    validate_timezone,
    get_date_string
)


class TestConvertUtcToTimezone:
    """Test cases for UTC to timezone conversion."""
    
    def test_convert_to_eastern(self):
        """Test conversion to America/New_York."""
        # January 1, 2025, 00:00 UTC = December 31, 2024, 19:00 EST
        utc_timestamp = 1735689600
        result = convert_utc_to_timezone(utc_timestamp, 'America/New_York')
        
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 31
        assert result.hour == 19
    
    def test_convert_to_utc(self):
        """Test conversion to UTC."""
        utc_timestamp = 1735689600
        result = convert_utc_to_timezone(utc_timestamp, 'UTC')
        
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 0
    
    def test_invalid_timezone_fallback(self):
        """Test that invalid timezone falls back gracefully."""
        utc_timestamp = 1735689600
        result = convert_utc_to_timezone(utc_timestamp, 'Invalid/Timezone')
        
        # Should return UTC time without crashing
        assert isinstance(result, datetime)


class TestGetTimeOfDayCategory:
    """Test cases for time of day categorization."""
    
    def test_morning_category(self):
        """Test morning hours (6am - 2pm)."""
        # Create timezone-aware datetime
        tz = pytz.timezone('America/New_York')
        
        # 8 AM
        dt = tz.localize(datetime(2025, 1, 1, 8, 0))
        assert get_time_of_day_category(dt) == 'morning'
        
        # 6 AM (boundary)
        dt = tz.localize(datetime(2025, 1, 1, 6, 0))
        assert get_time_of_day_category(dt) == 'morning'
        
        # 1 PM
        dt = tz.localize(datetime(2025, 1, 1, 13, 0))
        assert get_time_of_day_category(dt) == 'morning'
    
    def test_afternoon_category(self):
        """Test afternoon hours (2pm - 10pm)."""
        tz = pytz.timezone('America/New_York')
        
        # 4 PM
        dt = tz.localize(datetime(2025, 1, 1, 16, 0))
        assert get_time_of_day_category(dt) == 'afternoon'
        
        # 2 PM (boundary)
        dt = tz.localize(datetime(2025, 1, 1, 14, 0))
        assert get_time_of_day_category(dt) == 'afternoon'
        
        # 9 PM
        dt = tz.localize(datetime(2025, 1, 1, 21, 0))
        assert get_time_of_day_category(dt) == 'afternoon'
    
    def test_night_category(self):
        """Test night hours (10pm - 6am)."""
        tz = pytz.timezone('America/New_York')
        
        # 11 PM
        dt = tz.localize(datetime(2025, 1, 1, 23, 0))
        assert get_time_of_day_category(dt) == 'night'
        
        # 10 PM (boundary)
        dt = tz.localize(datetime(2025, 1, 1, 22, 0))
        assert get_time_of_day_category(dt) == 'night'
        
        # 3 AM
        dt = tz.localize(datetime(2025, 1, 1, 3, 0))
        assert get_time_of_day_category(dt) == 'night'
        
        # 5 AM
        dt = tz.localize(datetime(2025, 1, 1, 5, 0))
        assert get_time_of_day_category(dt) == 'night'


class TestValidateTimezone:
    """Test cases for timezone validation."""
    
    def test_valid_timezones(self):
        """Test valid timezone strings."""
        assert validate_timezone('UTC')
        assert validate_timezone('America/New_York')
        assert validate_timezone('Europe/London')
        assert validate_timezone('Asia/Tokyo')
    
    def test_invalid_timezones(self):
        """Test invalid timezone strings."""
        assert not validate_timezone('Invalid/Timezone')
        assert not validate_timezone('')
        assert not validate_timezone(None)


class TestGetDateString:
    """Test cases for date string formatting."""
    
    def test_date_string_format(self):
        """Test date string formatting."""
        dt = datetime(2025, 1, 15, 10, 30, 45)
        result = get_date_string(dt)
        
        assert result == '2025-01-15'
    
    def test_date_string_single_digit_month_day(self):
        """Test date string with single digit month and day."""
        dt = datetime(2025, 3, 5, 10, 30, 45)
        result = get_date_string(dt)
        
        assert result == '2025-03-05'
