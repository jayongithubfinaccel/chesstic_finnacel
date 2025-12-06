"""
API routes for chess data operations.
"""
from flask import request, jsonify
import requests
from app.routes import api_bp
from app.services.chess_service import ChessService
from app.services.analytics_service import AnalyticsService
from app.utils.validators import validate_username, validate_date_range, validate_timezone


@api_bp.route('/analyze', methods=['POST'])
def analyze_games():
    """
    Analyze chess games for a given username and date range.
    
    Expected JSON body:
    {
        "username": "chess.com username",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD"
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        username = data.get('username')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not validate_username(username):
            return jsonify({'error': 'Invalid username'}), 400
            
        if not validate_date_range(start_date, end_date):
            return jsonify({'error': 'Invalid date range'}), 400
        
        # Fetch and analyze games
        chess_service = ChessService()
        result = chess_service.analyze_games(username, start_date, end_date)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/analyze/detailed', methods=['POST'])
def analyze_detailed():
    """
    Perform comprehensive analysis on chess games.
    
    Expected JSON body:
    {
        "username": "chess.com username",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "timezone": "America/New_York" (optional, defaults to UTC)
    }
    
    Returns:
    {
        "username": "username",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "timezone": "timezone",
        "total_games": number,
        "sections": {
            "overall_performance": {...},
            "color_performance": {...},
            "elo_progression": {...},
            "termination_wins": {...},
            "termination_losses": {...},
            "opening_performance": {...},
            "opponent_strength": {...},
            "time_of_day": {...}
        }
    }
    """
    try:
        # Parse request data
        data = request.get_json(silent=True)
        
        if data is None:
            return jsonify({
                'error': 'Request body must be JSON',
                'status': 'error'
            }), 400
        
        # Extract and validate parameters
        username = data.get('username')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        timezone = data.get('timezone', 'UTC')
        
        # Validate username
        if not username:
            return jsonify({
                'error': 'Username is required',
                'status': 'error'
            }), 400
        
        if not validate_username(username):
            return jsonify({
                'error': 'Invalid username format. Username must be 3-25 characters, alphanumeric with hyphens or underscores',
                'status': 'error'
            }), 400
        
        # Validate date range
        if not start_date or not end_date:
            return jsonify({
                'error': 'Both start_date and end_date are required',
                'status': 'error'
            }), 400
        
        if not validate_date_range(start_date, end_date):
            return jsonify({
                'error': 'Invalid date range. Dates must be in YYYY-MM-DD format, start must be before end, maximum 1 year range, and dates cannot be in the future',
                'status': 'error'
            }), 400
        
        # Validate timezone
        if not validate_timezone(timezone):
            return jsonify({
                'error': f'Invalid timezone: {timezone}. Please provide a valid IANA timezone string (e.g., America/New_York, UTC, Europe/London)',
                'status': 'error'
            }), 400
        
        # Check if user exists on Chess.com
        chess_service = ChessService()
        try:
            chess_service.get_player_profile(username)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({
                    'error': f'User "{username}" not found on Chess.com',
                    'status': 'error'
                }), 404
            else:
                return jsonify({
                    'error': 'Failed to connect to Chess.com API. Please try again later',
                    'status': 'error'
                }), 503
        
        # Fetch games from Chess.com
        try:
            result = chess_service.analyze_games(username, start_date, end_date)
            games = result.get('games', [])
        except requests.exceptions.RequestException as e:
            return jsonify({
                'error': 'Failed to fetch games from Chess.com. Please try again later',
                'status': 'error',
                'details': str(e)
            }), 503
        except Exception as e:
            return jsonify({
                'error': 'Error fetching game data',
                'status': 'error',
                'details': str(e)
            }), 500
        
        # Check if any games were found
        if not games:
            return jsonify({
                'username': username,
                'start_date': start_date,
                'end_date': end_date,
                'timezone': timezone,
                'total_games': 0,
                'message': f'No games found for {username} between {start_date} and {end_date}',
                'sections': {
                    'overall_performance': {'daily_stats': []},
                    'color_performance': {
                        'white': {'daily_stats': [], 'win_rate': 0, 'total': {'wins': 0, 'losses': 0, 'draws': 0}},
                        'black': {'daily_stats': [], 'win_rate': 0, 'total': {'wins': 0, 'losses': 0, 'draws': 0}}
                    },
                    'elo_progression': {'data_points': [], 'rating_change': 0},
                    'termination_wins': {},
                    'termination_losses': {},
                    'opening_performance': {'best_openings': [], 'worst_openings': []},
                    'opponent_strength': {
                        'lower_rated': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'win_rate': 0},
                        'similar_rated': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'win_rate': 0},
                        'higher_rated': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'win_rate': 0}
                    },
                    'time_of_day': {
                        'morning': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'win_rate': 0},
                        'afternoon': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'win_rate': 0},
                        'night': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'win_rate': 0}
                    }
                },
                'status': 'success'
            }), 200
        
        # Perform detailed analysis
        try:
            analytics_service = AnalyticsService()
            analysis = analytics_service.analyze_detailed(games, username, timezone)
            
            # Build response
            response = {
                'username': username,
                'start_date': start_date,
                'end_date': end_date,
                'timezone': timezone,
                'total_games': analysis['total_games'],
                'sections': analysis['sections'],
                'status': 'success'
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            return jsonify({
                'error': 'Error analyzing game data',
                'status': 'error',
                'details': str(e)
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'status': 'error',
            'details': str(e)
        }), 500


@api_bp.route('/player/<username>', methods=['GET'])
def get_player_profile(username):
    """Get player profile information."""
    try:
        if not validate_username(username):
            return jsonify({'error': 'Invalid username'}), 400
        
        chess_service = ChessService()
        profile = chess_service.get_player_profile(username)
        
        return jsonify(profile), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
