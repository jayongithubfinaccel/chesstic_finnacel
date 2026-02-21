"""
Configuration settings for the Flask application.
"""
import os
from datetime import timedelta


class Config:
    """Base configuration."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session settings
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Cache settings
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Rate limiting (requests per minute)
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_PER_MINUTE = 30
    
    # OpenAI API settings (Milestone 9: AI Chess Advisor)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL = 'gpt-4o-mini'  # Using gpt-4o-mini for cost efficiency
    OPENAI_MAX_TOKENS = 800  # Increased to 800 for 9+1 structured recommendations (PRD v2.1)
    OPENAI_TEMPERATURE = 0.7
    
    # Stockfish engine settings (Milestone 8: Mistake Analysis)
    STOCKFISH_PATH = os.environ.get('STOCKFISH_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stockfish.exe'))
    ENGINE_ANALYSIS_ENABLED = os.environ.get('ENGINE_ANALYSIS_ENABLED', 'True').lower() == 'true'
    ENGINE_DEPTH = int(os.environ.get('ENGINE_DEPTH', '12'))  # Reduced from 15 to 12 for faster analysis
    ENGINE_TIME_LIMIT = float(os.environ.get('ENGINE_TIME_LIMIT', '1.5'))  # Reduced from 2.0 to 1.5 seconds
    
    # AI Advisor cache settings
    AI_ADVICE_CACHE_TTL = 3600  # 1 hour in seconds


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    RATE_LIMIT_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
