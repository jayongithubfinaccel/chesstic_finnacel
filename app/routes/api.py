"""
API routes for chess data operations.
"""
from flask import request, jsonify, current_app
import requests
import traceback
import threading
import uuid
import os
import shutil
from app.routes import api_bp
from app.services.chess_service import ChessService
from app.services.analytics_service import AnalyticsService
from app.utils.validators import validate_username, validate_date_range, validate_timezone, get_date_range_error
from app.utils import task_manager
import logging

logger = logging.getLogger(__name__)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring.
    
    Returns status of all critical components:
    - app: Flask application
    - stockfish: Stockfish engine availability
    - chess_api: Chess.com API connectivity
    - openai: OpenAI API key configured
    - disk: Disk space
    """
    checks = {}
    overall_status = 'healthy'
    
    # Check 1: App is running (always true if we get here)
    checks['app'] = {'status': 'ok', 'detail': 'Flask application running'}
    
    # Check 2: Stockfish engine
    stockfish_path = current_app.config.get('STOCKFISH_PATH', 'stockfish')
    try:
        import chess.engine
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        engine.quit()
        checks['stockfish'] = {'status': 'ok', 'detail': f'Engine available at {stockfish_path}'}
    except Exception as e:
        checks['stockfish'] = {'status': 'error', 'detail': str(e), 'error_code': 'ERR_STOCKFISH_UNAVAILABLE'}
        overall_status = 'degraded'
    
    # Check 3: Chess.com API
    try:
        resp = requests.get('https://api.chess.com/pub/player/hikaru', timeout=5)
        if resp.status_code == 200:
            checks['chess_api'] = {'status': 'ok', 'detail': 'Chess.com API reachable'}
        else:
            checks['chess_api'] = {'status': 'warning', 'detail': f'Chess.com API returned {resp.status_code}', 'error_code': 'ERR_CHESS_API_STATUS'}
            overall_status = 'degraded'
    except requests.exceptions.RequestException as e:
        checks['chess_api'] = {'status': 'error', 'detail': str(e), 'error_code': 'ERR_CHESS_API_UNREACHABLE'}
        overall_status = 'degraded'
    
    # Check 4: OpenAI API key
    openai_key = current_app.config.get('OPENAI_API_KEY', '')
    if openai_key and openai_key != 'your_openai_api_key_here':
        checks['openai'] = {'status': 'ok', 'detail': 'API key configured'}
    else:
        checks['openai'] = {'status': 'warning', 'detail': 'API key not configured', 'error_code': 'ERR_OPENAI_NO_KEY'}
        if overall_status == 'healthy':
            overall_status = 'degraded'
    
    # Check 5: Disk space
    try:
        disk = shutil.disk_usage('/')
        free_gb = disk.free / (1024 ** 3)
        checks['disk'] = {'status': 'ok' if free_gb > 1 else 'warning', 'detail': f'{free_gb:.1f} GB free'}
        if free_gb < 1:
            checks['disk']['error_code'] = 'ERR_LOW_DISK_SPACE'
            overall_status = 'degraded'
    except Exception:
        checks['disk'] = {'status': 'unknown'}
    
    status_code = 200 if overall_status != 'unhealthy' else 503
    return jsonify({
        'status': overall_status,
        'checks': checks
    }), status_code


def run_mistake_analysis_background(task_id: str, games: list, username: str, analytics_service):
    """
    Run Stockfish mistake analysis in background thread.
    
    Args:
        task_id: Unique task identifier
        games: List of game dictionaries
        username: Player's Chess.com username
        analytics_service: AnalyticsService instance
    """
    try:
        logger.info(f"Starting background mistake analysis for task {task_id}")
        
        # Create a progress callback function
        def progress_callback(current: int, total: int):
            """Update task progress"""
            task_manager.update_task_progress(task_id, current, 'processing')
        
        # Run analysis with progress reporting
        result = analytics_service.mistake_analyzer.aggregate_mistake_analysis(
            games, username, progress_callback=progress_callback
        )
        
        # Identify weakest stage
        weakest_stage, reason = analytics_service.mistake_analyzer.get_weakest_stage(result)
        result['weakest_stage'] = weakest_stage
        result['weakest_stage_reason'] = reason
        
        # Store completed result
        task_manager.complete_task(task_id, result)
        logger.info(f"Background mistake analysis completed for task {task_id}")
        
    except Exception as e:
        logger.error(f"Error in background mistake analysis for task {task_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        task_manager.fail_task(task_id, str(e))


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
                'status': 'error',
                'error_code': 'ERR_INVALID_JSON'
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
                'status': 'error',
                'error_code': 'ERR_USERNAME_REQUIRED'
            }), 400
        
        if not validate_username(username):
            return jsonify({
                'error': 'Invalid username format. Username must be 3-25 characters, alphanumeric with hyphens or underscores',
                'status': 'error',
                'error_code': 'ERR_INVALID_USERNAME'
            }), 400
        
        # Validate date range
        if not start_date or not end_date:
            return jsonify({
                'error': 'Both start_date and end_date are required',
                'status': 'error',
                'error_code': 'ERR_DATE_REQUIRED'
            }), 400
        
        # PRD v2.2: Check for specific date range errors (30-day max)
        date_error = get_date_range_error(start_date, end_date)
        if date_error:
            return jsonify({
                'error': date_error,
                'status': 'error',
                'error_code': 'date_range_exceeded' if '30 days' in date_error else 'invalid_date_range'
            }), 400
        
        # Validate timezone
        if not validate_timezone(timezone):
            return jsonify({
                'error': f'Invalid timezone: {timezone}. Please provide a valid IANA timezone string (e.g., America/New_York, UTC, Europe/London)',
                'status': 'error',
                'error_code': 'ERR_INVALID_TIMEZONE'
            }), 400
        
        # Check if user exists on Chess.com
        chess_service = ChessService()
        try:
            chess_service.get_player_profile(username)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({
                    'error': f'User "{username}" not found on Chess.com',
                    'status': 'error',
                    'error_code': 'ERR_USER_NOT_FOUND'
                }), 404
            else:
                return jsonify({
                    'error': 'Failed to connect to Chess.com API. Please try again later',
                    'status': 'error',
                    'error_code': 'ERR_CHESS_API_ERROR'
                }), 503
        
        # Fetch games from Chess.com
        try:
            logger.info(f"Fetching games for {username} from {start_date} to {end_date}")
            result = chess_service.analyze_games(username, start_date, end_date)
            games = result.get('games', [])
            logger.info(f"Fetched {len(games)} games successfully")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching games: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'error': 'Failed to fetch games from Chess.com. Please try again later',
                'status': 'error',
                'error_code': 'ERR_CHESS_API_FETCH',
                'details': str(e)
            }), 503
        except Exception as e:
            logger.error(f"Unexpected error fetching games: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'error': 'Error fetching game data',
                'status': 'error',
                'error_code': 'ERR_GAME_FETCH',
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
            # Get configuration from app config
            config = current_app.config
            
            # Extract analysis options from request (optional)
            include_mistake_analysis = data.get('include_mistake_analysis', True)
            include_ai_advice = data.get('include_ai_advice', True)
            
            # Initialize analytics service with configuration
            analytics_service = AnalyticsService(
                stockfish_path=config.get('STOCKFISH_PATH', 'stockfish'),
                engine_depth=config.get('ENGINE_DEPTH', 8),
                engine_time_limit=config.get('ENGINE_TIME_LIMIT', 0.2),
                engine_nodes=config.get('ENGINE_NODES', 50000),  # Iteration 12
                engine_enabled=config.get('ENGINE_ANALYSIS_ENABLED', True) and include_mistake_analysis,
                openai_api_key=config.get('OPENAI_API_KEY', ''),
                openai_model=config.get('OPENAI_MODEL', 'gpt-4o-mini'),
                use_lichess_cloud=config.get('USE_LICHESS_CLOUD', True),
                lichess_timeout=config.get('LICHESS_API_TIMEOUT', 5.0),
                max_analysis_games=config.get('MAX_ANALYSIS_GAMES', 10),  # Iteration 12
                moves_per_game=config.get('MOVES_PER_GAME', 15)  # Iteration 12
            )
            
            # Format date range for AI advisor context
            date_range = f"{start_date} to {end_date}"
            
            # Perform analysis (without mistake analysis initially)
            logger.info(f"Starting analysis for {username}: {date_range}, {len(games)} games")
            logger.info(f"Analysis options: mistake_analysis={include_mistake_analysis}, ai_advice={include_ai_advice}")
            
            try:
                # Run fast analysis first (no Stockfish - returns immediately)
                analysis = analytics_service.analyze_detailed(
                    games, 
                    username, 
                    timezone,
                    include_mistake_analysis=False,  # Skip for immediate response
                    include_ai_advice=include_ai_advice,
                    date_range=date_range
                )
                logger.info(f"Fast analysis complete: {analysis['total_games']} games processed")
                
                # If mistake analysis requested, start in background
                if include_mistake_analysis:
                    # Generate unique task ID
                    task_id = str(uuid.uuid4())
                    
                    # Calculate estimated games to analyze
                    total_games = len(games)
                    if total_games < 50:
                        games_to_analyze = total_games
                    else:
                        games_to_analyze = max(10, min(50, int(total_games * 0.20)))
                    
                    estimated_time = games_to_analyze * 2.5  # 2.5 seconds per game
                    
                    # Create task
                    task_manager.create_task(
                        task_id, 
                        total_items=games_to_analyze,
                        metadata={
                            'username': username,
                            'total_games': total_games,
                            'games_to_analyze': games_to_analyze
                        }
                    )
                    
                    # Start background thread
                    thread = threading.Thread(
                        target=run_mistake_analysis_background,
                        args=(task_id, games, username, analytics_service),
                        daemon=True
                    )
                    thread.start()
                    logger.info(f"Started background mistake analysis thread for task {task_id}")
                    
                    # Add processing status to response
                    analysis['sections']['mistake_analysis'] = {
                        'status': 'processing',
                        'task_id': task_id,
                        'estimated_time': f"{int(estimated_time)} seconds",
                        'message': f"Analyzing {games_to_analyze} games for mistakes..."
                    }
                
            except Exception as analysis_error:
                logger.error(f"Error in analyze_detailed: {analysis_error}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
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
            
            # Cleanup old tasks periodically
            task_manager.cleanup_old_tasks()
            
            return jsonify(response), 200
            
        except Exception as e:
            logger.error(f"Error analyzing game data: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'error': 'Error analyzing game data',
                'status': 'error',
                'error_code': 'ERR_ANALYSIS_FAILED',
                'details': str(e)
            }), 500
    
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error',
            'error_code': 'ERR_INTERNAL',
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


@api_bp.route('/analyze/mistake-status/<task_id>', methods=['GET'])
def get_mistake_analysis_status(task_id):
    """
    Get status of background mistake analysis task.
    
    Args:
        task_id: Unique task identifier from initial analysis request
        
    Returns:
        JSON response with task status:
        - processing: Task still running (with progress info)
        - completed: Task finished (with analysis data)
        - error: Task failed (with error message)
        - not_found: Task ID doesn't exist
    """
    try:
        logger.info(f"Status check for task {task_id}")
        
        # Get task status from task manager
        status = task_manager.get_task_status(task_id)
        
        if status is None:
            return jsonify({
                'status': 'not_found',
                'error': 'Task not found. It may have expired (tasks are kept for 1 hour).'
            }), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'details': str(e)
        }), 500
