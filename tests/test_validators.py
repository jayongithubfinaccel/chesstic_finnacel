"""
Unit tests for validators module.
"""
import pytest
from datetime import datetime, timedelta
from app.utils.validators import validate_username, validate_date_range, validate_timezone


class TestValidateUsername:
    """Test cases for username validation."""
    
    def test_valid_username(self):
        """Test valid usernames."""
        assert validate_username('validuser')
        assert validate_username('user123')
        assert validate_username('test-user')
        assert validate_username('test_user')
        assert validate_username('User_Name-123')
    
    def test_invalid_username_too_short(self):
        """Test username that is too short."""
        assert not validate_username('ab')
        assert not validate_username('a')
    
    def test_invalid_username_too_long(self):
        """Test username that is too long."""
        assert not validate_username('a' * 26)
    
    def test_invalid_username_special_chars(self):
        """Test username with invalid characters."""
        assert not validate_username('user@name')
        assert not validate_username('user name')
        assert not validate_username('user!name')
    
    def test_invalid_username_none(self):
        """Test None username."""
        assert not validate_username(None)
    
    def test_invalid_username_empty(self):
        """Test empty username."""
        assert not validate_username('')


class TestValidateDateRange:
    """Test cases for date range validation."""
    
    def test_valid_date_range(self):
        """Test valid date ranges."""
        assert validate_date_range('2024-01-01', '2024-01-31')
        assert validate_date_range('2024-06-15', '2024-06-20')
    
    def test_invalid_date_range_start_after_end(self):
        """Test start date after end date."""
        assert not validate_date_range('2024-02-01', '2024-01-01')
    
    def test_invalid_date_format(self):
        """Test invalid date formats."""
        assert not validate_date_range('01-01-2024', '31-01-2024')
        assert not validate_date_range('2024/01/01', '2024/01/31')
    
    def test_invalid_date_none(self):
        """Test None dates."""
        assert not validate_date_range(None, '2024-01-31')
        assert not validate_date_range('2024-01-01', None)
        assert not validate_date_range(None, None)
    
    def test_invalid_date_empty(self):
        """Test empty dates."""
        assert not validate_date_range('', '2024-01-31')
        assert not validate_date_range('2024-01-01', '')
    
    def test_invalid_date_range_too_long(self):
        """Test date range longer than 1 year."""
        start = datetime.now() - timedelta(days=400)
        end = datetime.now() - timedelta(days=1)
        assert not validate_date_range(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))


class TestValidateTimezone:
    """Test cases for timezone validation."""
    
    def test_valid_timezones(self):
        """Test valid timezone strings."""
        assert validate_timezone('UTC')
        assert validate_timezone('America/New_York')
        assert validate_timezone('Europe/London')
        assert validate_timezone('Asia/Tokyo')
        assert validate_timezone('Australia/Sydney')
    
    def test_invalid_timezone(self):
        """Test invalid timezone strings."""
        assert not validate_timezone('Invalid/Timezone')
        assert not validate_timezone('Not_A_Timezone')
        assert not validate_timezone('America/InvalidCity')
    
    def test_invalid_timezone_none(self):
        """Test None timezone."""
        assert not validate_timezone(None)
    
    def test_invalid_timezone_empty(self):
        """Test empty timezone."""
        assert not validate_timezone('')
