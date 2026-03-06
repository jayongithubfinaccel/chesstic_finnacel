"""
Flask application factory for Chess Analytics website.
"""
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config


def _setup_logging(app):
    """Configure structured logging for production error monitoring."""
    log_level = logging.DEBUG if app.debug else logging.INFO
    
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger for the app
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    
    # Also configure the app's modules
    for module_name in ['app.routes.api', 'app.services', 'app.utils']:
        module_logger = logging.getLogger(module_name)
        module_logger.handlers.clear()
        module_logger.addHandler(handler)
        module_logger.setLevel(log_level)


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    # Get the path to the project root (parent of app directory)
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__,
                template_folder=os.path.join(root_path, 'templates'),
                static_folder=os.path.join(root_path, 'static'))
    app.config.from_object(config_class)
    
    # Setup structured logging
    _setup_logging(app)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register global error handlers with error codes
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found', 'error_code': 'ERR_NOT_FOUND', 'status': 'error'}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f'Internal server error: {e}')
        return jsonify({'error': 'Internal server error', 'error_code': 'ERR_INTERNAL', 'status': 'error'}), 500
    
    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({'error': 'Too many requests', 'error_code': 'ERR_RATE_LIMIT', 'status': 'error'}), 429
    
    return app
