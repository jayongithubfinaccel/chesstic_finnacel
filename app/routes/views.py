"""
View routes for rendering HTML templates.
Iteration 11: Added GTM/GA configuration pass-through to templates
Iteration 11.1: Analytics dashboard is the homepage served at /
Deep Check Analysis: Added /deep-analysis route
"""
from flask import render_template, current_app, redirect, url_for, request
from app.routes import main_bp


@main_bp.route('/')
@main_bp.route('/analytics')
def analytics():
    """Render the analytics dashboard page (homepage)."""
    return render_template(
        'analytics.html',
        gtm_enabled=current_app.config.get('GTM_ENABLED', False),
        gtm_container_id=current_app.config.get('GTM_CONTAINER_ID', ''),
        ga_measurement_id=current_app.config.get('GA_MEASUREMENT_ID', ''),
        mistake_analysis_enabled=current_app.config.get('MISTAKE_ANALYSIS_UI_ENABLED', False)
    )


@main_bp.route('/deep-analysis')
def deep_analysis():
    """Render the deep check analysis page."""
    username = request.args.get('username', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    return render_template(
        'deep_analysis.html',
        username=username,
        start_date=start_date,
        end_date=end_date,
        gtm_enabled=current_app.config.get('GTM_ENABLED', False),
        gtm_container_id=current_app.config.get('GTM_CONTAINER_ID', ''),
        ga_measurement_id=current_app.config.get('GA_MEASUREMENT_ID', ''),
    )
