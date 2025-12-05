"""
Flask application factory for Chess Analytics website.
"""
import os
from flask import Flask
from flask_cors import CORS
from config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    # Get the path to the project root (parent of app directory)
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__,
                template_folder=os.path.join(root_path, 'templates'),
                static_folder=os.path.join(root_path, 'static'))
    app.config.from_object(config_class)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
