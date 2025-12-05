"""
Unit tests for validators module.
"""
import pytest
from app.utils.validators import validate_username, validate_date_range


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
