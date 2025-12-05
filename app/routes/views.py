"""
View routes for rendering HTML templates.
"""
from flask import render_template
from app.routes import main_bp


@main_bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@main_bp.route('/analytics')
def analytics():
    """Render the analytics page."""
    return render_template('analytics.html')
