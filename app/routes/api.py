"""
API routes for chess data operations.
"""
from flask import request, jsonify
from app.routes import api_bp
from app.services.chess_service import ChessService
from app.utils.validators import validate_username, validate_date_range


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
