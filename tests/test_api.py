"""
Integration tests for API endpoints.
"""
import pytest
import json
from datetime import datetime, timedelta
from app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


class TestAnalyzeDetailedEndpoint:
    """Test cases for /api/analyze/detailed endpoint."""
    
    def test_analyze_detailed_missing_body(self, client):
        """Test endpoint with missing request body."""
        response = client.post('/api/analyze/detailed')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'JSON' in data['error']
    
    def test_analyze_detailed_missing_username(self, client):
        """Test endpoint with missing username."""
        response = client.post(
            '/api/analyze/detailed',
            json={
                'start_date': '2024-01-01',
                'end_date': '2024-01-31'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'username' in data['error'].lower()
    
    def test_analyze_detailed_invalid_username(self, client):
        """Test endpoint with invalid username format."""
        response = client.post(
            '/api/analyze/detailed',
            json={
                'username': 'ab',  # Too short
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'timezone': 'UTC'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'username' in data['error'].lower()
    
    def test_analyze_detailed_missing_dates(self, client):
        """Test endpoint with missing dates."""
        response = client.post(
            '/api/analyze/detailed',
            json={
                'username': 'testuser'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'date' in data['error'].lower()
    
    def test_analyze_detailed_invalid_date_range(self, client):
        """Test endpoint with invalid date range."""
        response = client.post(
            '/api/analyze/detailed',
            json={
                'username': 'testuser',
                'start_date': '2024-12-31',
                'end_date': '2024-01-01',  # End before start
                'timezone': 'UTC'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'date range' in data['error'].lower()
    
    def test_analyze_detailed_date_range_too_long(self, client):
        """Test endpoint with date range longer than 1 year."""
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=400)
        
        response = client.post(
            '/api/analyze/detailed',
            json={
                'username': 'testuser',
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'timezone': 'UTC'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'date range' in data['error'].lower()
    
    def test_analyze_detailed_invalid_timezone(self, client):
        """Test endpoint with invalid timezone."""
        response = client.post(
            '/api/analyze/detailed',
            json={
                'username': 'testuser',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'timezone': 'Invalid/Timezone'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'timezone' in data['error'].lower()
    
    def test_analyze_detailed_default_timezone(self, client):
        """Test endpoint uses UTC as default timezone."""
        # Note: This will make real API call, so it might fail if user doesn't exist
        # or if there are no games. That's okay for this test structure.
        response = client.post(
            '/api/analyze/detailed',
            json={
                'username': 'testuser123',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31'
            }
        )
        
        # We accept either 404 (user not found) or 200 (success)
        # The important thing is that it didn't fail with 400 (validation error)
        assert response.status_code in [200, 404, 503]
    
    def test_analyze_detailed_valid_request_structure(self, client):
        """Test that valid request structure is accepted."""
        response = client.post(
            '/api/analyze/detailed',
            json={
                'username': 'hikaru',  # Known Chess.com user
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'timezone': 'America/New_York'
            }
        )
        
        # Should either succeed or fail gracefully (not validation error)
        assert response.status_code in [200, 503, 504]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'username' in data
            assert 'total_games' in data
            assert 'sections' in data
            assert 'status' in data
            assert data['status'] == 'success'


class TestAnalyzeEndpoint:
    """Test cases for /api/analyze endpoint (existing)."""
    
    def test_analyze_invalid_username(self, client):
        """Test analyze endpoint with invalid username."""
        response = client.post(
            '/api/analyze',
            json={
                'username': 'ab',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31'
            }
        )
        
        assert response.status_code == 400
    
    def test_analyze_invalid_date_range(self, client):
        """Test analyze endpoint with invalid date range."""
        response = client.post(
            '/api/analyze',
            json={
                'username': 'testuser',
                'start_date': '2024-12-31',
                'end_date': '2024-01-01'
            }
        )
        
        assert response.status_code == 400


class TestPlayerProfileEndpoint:
    """Test cases for /api/player/<username> endpoint."""
    
    def test_player_profile_invalid_username(self, client):
        """Test player profile with invalid username."""
        response = client.get('/api/player/ab')
        
        assert response.status_code == 400
    
    def test_player_profile_valid_format(self, client):
        """Test player profile with valid username format."""
        response = client.get('/api/player/hikaru')
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 404, 500, 503]
