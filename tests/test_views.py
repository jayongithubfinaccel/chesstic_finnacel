"""
Tests for view routes with GTM configuration.
Iteration 11: Test GTM configuration pass-through to templates
"""
import pytest
from flask import Flask
from app import create_app
from config import TestingConfig


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = create_app(TestingConfig)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestViewsWithGTM:
    """Test view routes with GTM configuration."""
    
    def test_index_route_exists(self, client):
        """Test that index route returns 200."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_analytics_route_exists(self, client):
        """Test that analytics route returns 200."""
        response = client.get('/analytics')
        assert response.status_code == 200
    
    def test_index_with_gtm_enabled(self, app, client):
        """Test GTM script appears when enabled."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = 'GT-TESTID'
        
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # Check for GTM script in head - container ID is passed as a parameter
        assert "'GT-TESTID'" in html or '"GT-TESTID"' in html
        assert 'Google Tag Manager' in html
        
        # Check for noscript fallback
        assert 'googletagmanager.com/ns.html?id=GT-TESTID' in html
    
    def test_analytics_with_gtm_enabled(self, app, client):
        """Test GTM script appears in analytics page when enabled."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = 'GT-TESTID'
        
        response = client.get('/analytics')
        html = response.data.decode('utf-8')
        
        # Check for GTM script - container ID is passed as a parameter
        assert "'GT-TESTID'" in html or '"GT-TESTID"' in html
        assert 'noscript' in html
    
    def test_index_with_gtm_disabled(self, app, client):
        """Test GTM script absent when disabled."""
        app.config['GTM_ENABLED'] = False
        app.config['GTM_CONTAINER_ID'] = 'GT-TESTID'
        
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # GTM should not appear
        assert 'googletagmanager.com' not in html
        assert 'GT-TESTID' not in html
    
    def test_analytics_with_gtm_disabled(self, app, client):
        """Test GTM script absent in analytics when disabled."""
        app.config['GTM_ENABLED'] = False
        app.config['GTM_CONTAINER_ID'] = 'GT-TESTID'
        
        response = client.get('/analytics')
        html = response.data.decode('utf-8')
        
        # GTM should not appear
        assert 'googletagmanager.com' not in html
    
    def test_index_with_no_gtm_container_id(self, app, client):
        """Test GTM script absent when container ID missing."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = ''
        
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # GTM should not appear without container ID
        assert 'googletagmanager.com' not in html
    
    def test_analytics_with_no_gtm_container_id(self, app, client):
        """Test GTM script absent in analytics when container ID missing."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = ''
        
        response = client.get('/analytics')
        html = response.data.decode('utf-8')
        
        # GTM should not appear
        assert 'googletagmanager.com' not in html
    
    def test_index_with_custom_container_id(self, app, client):
        """Test custom GTM container ID is used correctly."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = 'GT-CUSTOM123'
        
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # Check custom ID appears - container ID is passed as a parameter
        assert "'GT-CUSTOM123'" in html or '"GT-CUSTOM123"' in html
        assert 'googletagmanager.com/ns.html?id=GT-CUSTOM123' in html
    
    def test_analytics_with_custom_container_id(self, app, client):
        """Test custom GTM container ID in analytics page."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = 'GT-CUSTOM123'
        
        response = client.get('/analytics')
        html = response.data.decode('utf-8')
        
        # Check custom ID appears
        assert 'GT-CUSTOM123' in html
    
    def test_index_has_required_elements(self, client):
        """Test index page has required HTML elements."""
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # Check for basic page elements
        assert '<html' in html
        assert '<head>' in html
        assert '<body>' in html
        assert 'Chess Analytics' in html
    
    def test_analytics_has_required_elements(self, client):
        """Test analytics page has required HTML elements."""
        response = client.get('/analytics')
        html = response.data.decode('utf-8')
        
        # Check for basic page elements
        assert '<html' in html
        assert '<head>' in html
        assert '<body>' in html
        assert 'Analytics Dashboard' in html or 'Chess Analytics' in html
    
    def test_gtm_script_placement_in_head(self, app, client):
        """Test GTM script appears early in head section."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = 'GT-TESTID'
        
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # Find positions
        head_pos = html.find('<head>')
        gtm_pos = html.find('<!-- Google Tag Manager -->')
        charset_pos = html.find('<meta charset')
        
        # GTM should be after <head> but before other meta tags
        assert head_pos < gtm_pos < charset_pos
    
    def test_gtm_noscript_placement(self, app, client):
        """Test GTM noscript appears right after body tag."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = 'GT-TESTID'
        
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # Find positions
        body_pos = html.find('<body>')
        noscript_pos = html.find('<!-- Google Tag Manager (noscript) -->')
        
        # Noscript should be right after <body>
        # Allow for some whitespace
        assert body_pos < noscript_pos
        assert noscript_pos - body_pos < 50  # Should be within 50 chars
    
    def test_multiple_gtm_container_ids_not_present(self, app, client):
        """Test that changing container ID doesn't leave old IDs."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = 'GT-NEWID'
        
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # Should only have new ID
        assert 'GT-NEWID' in html
        # Old hardcoded ID should not be present
        assert 'GT-NFBTKHBS' not in html or app.config['GTM_CONTAINER_ID'] == 'GT-NFBTKHBS'
    
    def test_gtm_default_values(self, app, client):
        """Test default GTM configuration values."""
        # Don't set any GTM config - use defaults
        response = client.get('/')
        
        # Should still work (GTM may or may not appear based on defaults)
        assert response.status_code == 200


class TestViewsContentType:
    """Test view response content types."""
    
    def test_index_content_type(self, client):
        """Test index returns HTML content type."""
        response = client.get('/')
        assert response.content_type.startswith('text/html')
    
    def test_analytics_content_type(self, client):
        """Test analytics returns HTML content type."""
        response = client.get('/analytics')
        assert response.content_type.startswith('text/html')


class TestViewsSecurity:
    """Test view security headers."""
    
    def test_gtm_script_attributes(self, app, client):
        """Test GTM script has correct attributes."""
        app.config['GTM_ENABLED'] = True
        app.config['GTM_CONTAINER_ID'] = 'GT-TESTID'
        
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # Check for async loading
        assert 'j.async=true' in html
