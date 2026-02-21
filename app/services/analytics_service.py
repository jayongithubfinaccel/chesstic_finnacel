"""
Analytics service for comprehensive chess game analysis.
"""
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import chess.pgn
from io import StringIO
import re
import logging

from app.utils.timezone_utils import (
    convert_utc_to_timezone, 
    get_time_of_day_category,
    get_date_string
)
from app.services.mistake_analysis_service import MistakeAnalysisService
from app.services.chess_advisor_service import ChessAdvisorService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for advanced chess analytics calculations."""
    
    @staticmethod
    def _normalize_result(result: str) -> str:
        """
        Normalize Chess.com API result values to consistent format.
        
        Chess.com API result values:
        - Wins: 'win'
        - Losses: 'checkmated', 'timeout', 'resigned', 'abandoned', 'lose'
        - Draws: 'agreed', 'repetition', 'timevsinsufficient', 'insufficient', 'stalemate', '50move'
        
        Returns: 'win', 'loss', or 'draw'
        """
        result_lower = result.lower() if result else ''
        
        if result_lower == 'win':
            return 'win'
        elif result_lower in ['checkmated', 'timeout', 'resigned', 'abandoned', 'lose']:
            return 'loss'
        else:
            # All other results are draws
            return 'draw'
    
    def __init__(self, stockfish_path: str = 'stockfish', engine_depth: int = 12,
                 engine_enabled: bool = True, openai_api_key: str = '',
                 openai_model: str = 'gpt-4o-mini'):
        """
        Initialize analytics service.
        
        Args:
            stockfish_path: Path to Stockfish executable
            engine_depth: Engine analysis depth (default: 12 in PRD v2.2)
            engine_enabled: Whether to enable engine analysis
            openai_api_key: OpenAI API key for AI advisor
            openai_model: OpenAI model to use
        """
        self.mistake_analyzer = MistakeAnalysisService(
            stockfish_path=stockfish_path,
            engine_depth=engine_depth,
            enabled=engine_enabled
        )
        self.ai_advisor = ChessAdvisorService(
            api_key=openai_api_key,
            model=openai_model
        )
    
    def analyze_detailed(
        self, 
        games: List[Dict], 
        username: str, 
        timezone: str = 'UTC',
        include_mistake_analysis: bool = True,
        include_ai_advice: bool = True,
        date_range: str = ''
    ) -> Dict:
        """
        Perform comprehensive analysis on games.
        
        Args:
            games: List of game dictionaries from Chess.com API
            username: Player's Chess.com username
            timezone: User's timezone string
            include_mistake_analysis: Whether to include engine mistake analysis (Milestone 8)
            include_ai_advice: Whether to include AI advisor recommendations (Milestone 9)
            date_range: Date range string for AI advisor context
            
        Returns:
            Comprehensive analysis results for all sections including M8 & M9
        """
        if not games:
            return self._empty_analysis()
        
        # Analyze all games
        analyzed_games = self._parse_and_enrich_games(games, username, timezone)
        
        # Core sections (Milestones 1-7)
        sections = {
            'overall_performance': self._analyze_overall_performance(analyzed_games),
            'color_performance': self._analyze_color_performance(analyzed_games),
            'elo_progression': self._analyze_elo_progression(analyzed_games),
            'termination_wins': self._analyze_termination_wins(analyzed_games),
            'termination_losses': self._analyze_termination_losses(analyzed_games),
            'opening_performance': self._analyze_opening_performance(analyzed_games),
            'opponent_strength': self._analyze_opponent_strength(analyzed_games),
            'time_of_day': self._analyze_time_of_day(analyzed_games)
        }
        
        # Milestone 8: Mistake analysis by game stage
        if include_mistake_analysis:
            logger.info("Starting mistake analysis...")
            mistake_analysis = self.mistake_analyzer.aggregate_mistake_analysis(games, username)
            
            # Identify weakest stage
            weakest_stage, reason = self.mistake_analyzer.get_weakest_stage(mistake_analysis)
            mistake_analysis['weakest_stage'] = weakest_stage
            mistake_analysis['weakest_stage_reason'] = reason
            
            sections['mistake_analysis'] = mistake_analysis
            logger.info("Mistake analysis complete")
        
        # Build result
        result = {
            'total_games': len(analyzed_games),
            'sections': sections
        }
        
        # Milestone 9: AI-powered chess advisor
        if include_ai_advice:
            logger.info("Generating AI coaching advice...")
            ai_advice = self.ai_advisor.generate_advice(result, username, date_range)
            sections['ai_advice'] = ai_advice
            logger.info("AI advice generated")
        
        return result
    
    def _parse_and_enrich_games(
        self, 
        games: List[Dict], 
        username: str, 
        timezone: str
    ) -> List[Dict]:
        """
        Parse and enrich game data with additional information.
        
        Args:
            games: Raw game data from Chess.com API
            username: Player's username
            timezone: User's timezone
            
        Returns:
            List of enriched game dictionaries
        """
        enriched = []
        username_lower = username.lower()
        
        for game in games:
            white = game.get('white', {})
            black = game.get('black', {})
            
            # Determine player's color and opponent
            if white.get('username', '').lower() == username_lower:
                player_color = 'white'
                player_data = white
                opponent_data = black
            else:
                player_color = 'black'
                player_data = black
                opponent_data = white
            
            # Get result and normalize it
            raw_result = player_data.get('result', '')
            result = self._normalize_result(raw_result)
            
            # Convert timestamp to user's timezone
            end_time = game.get('end_time', 0)
            local_time = convert_utc_to_timezone(end_time, timezone)
            
            # Extract opening name from PGN
            opening_name = self._extract_opening_name(game.get('pgn', ''))
            
            # Extract termination type
            termination = self._extract_termination(game)
            
            enriched.append({
                'pgn': game.get('pgn', ''),
                'end_time': end_time,
                'local_time': local_time,
                'date': get_date_string(local_time),
                'time_of_day': get_time_of_day_category(local_time),
                'player_color': player_color,
                'result': result,
                'player_rating': player_data.get('rating', 0),
                'opponent_rating': opponent_data.get('rating', 0),
                'opponent_username': opponent_data.get('username', 'Unknown'),
                'time_control': game.get('time_control', 'unknown'),
                'time_class': game.get('time_class', 'unknown'),
                'opening_name': opening_name,
                'termination': termination,
                'url': game.get('url', '')
            })
        
        # Sort by date
        enriched.sort(key=lambda x: x['end_time'])
        
        return enriched
    
    def _extract_opening_name(self, pgn_string: str) -> str:
        """
        Extract opening name from PGN without ECO codes.
        
        Args:
            pgn_string: PGN string from game data
            
        Returns:
            Human-readable opening name or 'Unknown Opening'
        """
        if not pgn_string:
            return 'Unknown Opening'
        
        try:
            pgn = StringIO(pgn_string)
            game = chess.pgn.read_game(pgn)
            
            if game is None:
                return 'Unknown Opening'
            
            # Get opening name and ECO from headers
            eco = game.headers.get('ECO', '')
            opening_name = game.headers.get('Opening', '')
            eco_url = game.headers.get('ECOUrl', '')
            
            # Strategy 1: Use Opening header and remove ECO code
            if opening_name:
                # Remove ECO code pattern (e.g., "C00: ", "E04: ")
                import re
                # Match ECO pattern at start: letter followed by 2 digits, optional colon/space
                cleaned_name = re.sub(r'^[A-E]\d{2}[\s:]*', '', opening_name).strip()
                
                if cleaned_name:
                    return cleaned_name
            
            # Strategy 2: Try to extract from ECOUrl (Chess.com specific)
            if eco_url:
                # ECOUrl format: https://www.chess.com/openings/...
                # Extract the path and convert to readable name
                try:
                    path = eco_url.split('/openings/')[-1]
                    # Convert URL slug to readable name
                    readable = path.replace('-', ' ').title()
                    # Remove trailing numbers and clean up
                    readable = re.sub(r'\s+\d+$', '', readable).strip()
                    if readable and len(readable) > 2:
                        return readable
                except:
                    pass
            
            # Strategy 3: Identify from first moves using common patterns
            board = game.board()
            moves = []
            for move in list(game.mainline_moves())[:10]:
                moves.append(board.san(move))
                board.push(move)
            
            if moves:
                opening_from_moves = self._identify_opening_from_moves(moves)
                if opening_from_moves != 'Unknown Opening':
                    return opening_from_moves
            
            # Last resort: return "Unknown Opening" instead of ECO code
            return 'Unknown Opening'
            
        except Exception:
            return 'Unknown Opening'
    
    def _identify_opening_from_moves(self, moves: List[str]) -> str:
        """
        Identify opening from move sequence using common patterns.
        
        Args:
            moves: List of moves in SAN notation
            
        Returns:
            Opening name or 'Unknown Opening'
        """
        if not moves or len(moves) < 2:
            return 'Unknown Opening'
        
        # Common opening patterns (first 2-4 moves)
        move_str = ' '.join(moves[:4]).lower()
        
        # Comprehensive opening database based on first moves
        opening_patterns = {
            # King's Pawn Openings (1.e4)
            'e4 e5': {
                'nf3 nc6': {
                    'bb5': 'Ruy Lopez',
                    'bc4': 'Italian Game',
                    'd4': 'Scotch Game',
                    'nc3': 'Four Knights Game',
                },
                'nf3 nf6': 'Petrov Defense',
                'f4': 'King\'s Gambit',
                'bc4': 'Bishop\'s Opening',
                'd4': 'Center Game',
                'nc3': 'Vienna Game',
            },
            'e4 c5': 'Sicilian Defense',
            'e4 e6': 'French Defense',
            'e4 c6': 'Caro-Kann Defense',
            'e4 d5': 'Scandinavian Defense',
            'e4 nf6': 'Alekhine Defense',
            'e4 d6': 'Pirc Defense',
            'e4 g6': 'Modern Defense',
            'e4 nc6': 'Nimzowitsch Defense',
            
            # Queen's Pawn Openings (1.d4)
            'd4 d5': {
                'c4': {
                    'e6': 'Queen\'s Gambit Declined',
                    'c6': 'Slav Defense',
                    'dxc4': 'Queen\'s Gambit Accepted',
                    'nf6': 'Queen\'s Gambit Declined',
                },
                'nf3 nf6': 'Queen\'s Pawn Game',
                'e3': 'Queen\'s Pawn Game',
                'bf4': 'London System',
            },
            'd4 nf6': {
                'c4 e6': 'Queen\'s Indian Defense',
                'c4 g6': 'King\'s Indian Defense',
                'c4 c5': 'Benoni Defense',
                'nf3': 'Indian Game',
                'bf4': 'London System',
            },
            'd4 f5': 'Dutch Defense',
            'd4 g6': 'King\'s Indian Defense',
            'd4 e6': 'Queen\'s Pawn Game',
            'd4 d6': 'Pirc Defense',
            
            # Other Openings
            'nf3 d5': 'Réti Opening',
            'nf3 nf6': 'Réti Opening',
            'c4 e5': 'English Opening',
            'c4 nf6': 'English Opening',
            'c4 c5': 'English Opening',
            'f4': 'Bird Opening',
            'b3': 'Larsen Opening',
            'nc3 d5': 'Dunst Opening',
            'e3': 'Van\'t Kruijs Opening',
            'g3': 'King\'s Fianchetto Opening',
        }
        
        # Try to match patterns with decreasing move counts
        for depth in [4, 3, 2]:
            test_moves = ' '.join(moves[:depth]).lower()
            
            # Check exact match first
            if test_moves in opening_patterns:
                result = opening_patterns[test_moves]
                if isinstance(result, str):
                    return result
                # Continue checking deeper if dict
                
            # Check nested patterns
            for pattern, value in opening_patterns.items():
                if test_moves.startswith(pattern):
                    if isinstance(value, str):
                        return value
                    elif isinstance(value, dict):
                        # Check next level
                        remaining = test_moves[len(pattern):].strip()
                        for sub_pattern, opening_name in value.items():
                            if remaining.startswith(sub_pattern):
                                if isinstance(opening_name, str):
                                    return opening_name
                                elif isinstance(opening_name, dict):
                                    # Check third level
                                    remaining2 = remaining[len(sub_pattern):].strip()
                                    for sub2_pattern, final_name in opening_name.items():
                                        if remaining2.startswith(sub2_pattern):
                                            return final_name
        
        return 'Unknown Opening'
    
    def _extract_termination(self, game: Dict) -> str:
        """
        Extract termination type from game data.
        
        Args:
            game: Game dictionary
            
        Returns:
            Termination type: 'checkmate', 'timeout', 'resignation', 'abandoned', 'agreed', 'repetition', 'insufficient', 'stalemate', 'other'
        """
        # Try to parse from PGN
        pgn_string = game.get('pgn', '')
        if pgn_string:
            try:
                pgn = StringIO(pgn_string)
                game_obj = chess.pgn.read_game(pgn)
                if game_obj:
                    termination = game_obj.headers.get('Termination', '').lower()
                    
                    if 'checkmate' in termination or 'won by checkmate' in termination:
                        return 'checkmate'
                    elif 'time' in termination or 'timeout' in termination:
                        return 'timeout'
                    elif 'resignation' in termination or 'resigned' in termination:
                        return 'resignation'
                    elif 'abandoned' in termination:
                        return 'abandoned'
                    elif 'agreement' in termination or 'agreed' in termination:
                        return 'agreed'
                    elif 'repetition' in termination:
                        return 'repetition'
                    elif 'insufficient' in termination:
                        return 'insufficient'
                    elif 'stalemate' in termination:
                        return 'stalemate'
            except Exception:
                pass
        
        return 'other'
    
    def _analyze_overall_performance(self, games: List[Dict]) -> Dict:
        """
        Analyze overall win/loss/draw performance over time.
        
        Returns daily aggregated statistics and overall metrics.
        """
        daily_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0})
        total_wins = 0
        total_losses = 0
        total_draws = 0
        total_rating = 0
        rating_count = 0
        
        for game in games:
            date = game['date']
            result = game['result']
            
            # Track totals
            if result == 'win':
                daily_stats[date]['wins'] += 1
                total_wins += 1
            elif result == 'loss':
                daily_stats[date]['losses'] += 1
                total_losses += 1
            else:  # result == 'draw'
                daily_stats[date]['draws'] += 1
                total_draws += 1
            
            # Track ratings
            if game.get('player_rating', 0) > 0:
                total_rating += game['player_rating']
                rating_count += 1
        
        # Convert to list format
        daily_list = []
        for date in sorted(daily_stats.keys()):
            stats = daily_stats[date]
            daily_list.append({
                'date': date,
                'wins': stats['wins'],
                'losses': stats['losses'],
                'draws': stats['draws']
            })
        
        # Calculate metrics
        total_games = total_wins + total_losses + total_draws
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        avg_rating = (total_rating / rating_count) if rating_count > 0 else 0
        
        # Get rating change
        start_rating = games[0].get('player_rating', 0) if games else 0
        end_rating = games[-1].get('player_rating', 0) if games else 0
        rating_change = end_rating - start_rating
        
        # Determine trend
        if rating_change > 10:
            rating_trend = "Improving"
        elif rating_change < -10:
            rating_trend = "Declining"
        else:
            rating_trend = "Stable"
        
        return {
            'daily_stats': daily_list,
            'win_rate': round(win_rate, 2),
            'total': {
                'wins': total_wins,
                'losses': total_losses,
                'draws': total_draws
            },
            'avg_rating': round(avg_rating, 2),
            'rating_change': round(rating_change, 2),
            'rating_trend': rating_trend
        }
    
    def _analyze_color_performance(self, games: List[Dict]) -> Dict:
        """Analyze performance by color (white vs black).
        
        Iteration 5: Added explicit W/L/D counts and total_games to summary.
        """
        white_daily = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0})
        black_daily = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0})
        
        white_total = {'wins': 0, 'losses': 0, 'draws': 0}
        black_total = {'wins': 0, 'losses': 0, 'draws': 0}
        
        for game in games:
            date = game['date']
            result = game['result']
            color = game['player_color']
            
            daily_dict = white_daily if color == 'white' else black_daily
            total_dict = white_total if color == 'white' else black_total
            
            if result == 'win':
                daily_dict[date]['wins'] += 1
                total_dict['wins'] += 1
            elif result == 'loss':
                daily_dict[date]['losses'] += 1
                total_dict['losses'] += 1
            else:  # result == 'draw'
                daily_dict[date]['draws'] += 1
                total_dict['draws'] += 1
        
        # Calculate win rates and totals
        white_games = sum(white_total.values())
        black_games = sum(black_total.values())
        
        white_win_rate = (white_total['wins'] / white_games * 100) if white_games > 0 else 0
        black_win_rate = (black_total['wins'] / black_games * 100) if black_games > 0 else 0
        
        return {
            'white': {
                'daily_stats': [{'date': d, **white_daily[d]} for d in sorted(white_daily.keys())],
                'win_rate': round(white_win_rate, 2),
                'total_games': white_games,  # Iteration 5: Added
                'wins': white_total['wins'],  # Iteration 5: Added
                'losses': white_total['losses'],  # Iteration 5: Added
                'draws': white_total['draws'],  # Iteration 5: Added
                'total': white_total  # Keep for backward compatibility
            },
            'black': {
                'daily_stats': [{'date': d, **black_daily[d]} for d in sorted(black_daily.keys())],
                'win_rate': round(black_win_rate, 2),
                'total_games': black_games,  # Iteration 5: Added
                'wins': black_total['wins'],  # Iteration 5: Added
                'losses': black_total['losses'],  # Iteration 5: Added
                'draws': black_total['draws'],  # Iteration 5: Added
                'total': black_total  # Keep for backward compatibility
            }
        }
    
    def _analyze_elo_progression(self, games: List[Dict]) -> Dict:
        """Analyze Elo rating progression over time."""
        # Group by date and take the last rating of each day
        daily_ratings = {}
        all_ratings = []
        
        for game in games:
            date = game['date']
            rating = game['player_rating']
            # Keep updating - the last game of the day will be the final value
            daily_ratings[date] = rating
            all_ratings.append(rating)
        
        # Convert to list and sort by date
        data_points = [
            {'date': date, 'rating': rating}
            for date, rating in sorted(daily_ratings.items())
        ]
        
        # Calculate metrics
        start_rating = data_points[0]['rating'] if data_points else 0
        end_rating = data_points[-1]['rating'] if data_points else 0
        rating_change = end_rating - start_rating
        
        peak_rating = max(all_ratings) if all_ratings else 0
        lowest_rating = min(all_ratings) if all_ratings else 0
        
        return {
            'data_points': data_points,
            'rating_change': rating_change,
            'start_rating': start_rating,
            'end_rating': end_rating,
            'peak_rating': peak_rating,
            'lowest_rating': lowest_rating
        }
    
    def _analyze_termination_wins(self, games: List[Dict]) -> Dict:
        """Analyze how player wins games."""
        termination_counts = defaultdict(int)
        total_wins = 0
        
        for game in games:
            if game['result'] == 'win':
                termination_counts[game['termination']] += 1
                total_wins += 1
        
        return {
            'total_wins': total_wins,
            'breakdown': dict(termination_counts)
        }
    
    def _analyze_termination_losses(self, games: List[Dict]) -> Dict:
        """Analyze how player loses games."""
        termination_counts = defaultdict(int)
        total_losses = 0
        
        for game in games:
            if game['result'] == 'loss':
                termination_counts[game['termination']] += 1
                total_losses += 1
        
        return {
            'total_losses': total_losses,
            'breakdown': dict(termination_counts)
        }
    
    def _analyze_opening_performance(self, games: List[Dict]) -> Dict:
        """
        Analyze performance by chess opening, split by color.
        PRD v2.5: Changed to top 5 most common openings per color (frequency-based)
        with first 6 moves, Lichess URL, and Chess.com example game URL.
        """
        import urllib.parse
        
        # Track stats by color and opening
        white_opening_stats = defaultdict(lambda: {
            'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'sample_pgn': None, 'example_game_url': None
        })
        black_opening_stats = defaultdict(lambda: {
            'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'sample_pgn': None, 'example_game_url': None
        })
        
        for game in games:
            opening = game['opening_name']
            if opening == 'Unknown Opening':
                continue
            
            player_color = game['player_color']
            result = game['result']
            pgn = game.get('pgn', '')
            game_url = game.get('url', '')
            
            # Select the right stats dict based on color
            stats = white_opening_stats if player_color == 'white' else black_opening_stats
            
            stats[opening]['games'] += 1
            
            # Store a sample PGN and game URL for move extraction (first occurrence)
            if stats[opening]['sample_pgn'] is None and pgn:
                stats[opening]['sample_pgn'] = pgn
                stats[opening]['example_game_url'] = game_url  # Iteration 5: Added
            
            if result == 'win':
                stats[opening]['wins'] += 1
            elif result == 'loss':
                stats[opening]['losses'] += 1
            else:  # result == 'draw'
                stats[opening]['draws'] += 1
        
        def process_openings_by_color(opening_stats):
            """Process opening stats for a specific color.
            PRD v2.5: Return top 5 most common by games played (frequency-based).
            """
            all_openings = []
            for opening, stats in opening_stats.items():
                total = stats['games']
                win_rate = (stats['wins'] / total * 100) if total > 0 else 0
                
                # Extract first 6 moves from sample PGN
                first_moves = self._extract_first_six_moves(stats['sample_pgn'])
                fen = self._get_opening_position_fen(stats['sample_pgn'])
                
                # Generate Lichess URL
                lichess_url = ''
                if fen:
                    lichess_url = f"https://lichess.org/editor/{urllib.parse.quote(fen)}"
                
                all_openings.append({
                    'opening': opening,
                    'games': stats['games'],
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'draws': stats['draws'],
                    'win_rate': round(win_rate, 2),
                    'first_moves': first_moves,
                    'fen': fen,
                    'lichess_url': lichess_url,  # Iteration 5: Added
                    'example_game_url': stats['example_game_url']  # Iteration 5: Added
                })
            
            # PRD v2.5: Sort by games played (descending) for most common
            all_openings.sort(key=lambda x: x['games'], reverse=True)
            top_5_common = all_openings[:5]  # Top 5 most common (v2.5)
            
            return top_5_common
        
        # Iteration 5: Return separate lists for white and black
        return {
            'white': process_openings_by_color(white_opening_stats),
            'black': process_openings_by_color(black_opening_stats)
        }
    
    def _extract_first_six_moves(self, pgn_string: str) -> str:
        """
        Extract first 12 individual moves (6 full moves) in standard chess notation.
        Format example: "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5"
        
        Args:
            pgn_string: PGN string from game data
            
        Returns:
            String with first 12 moves in standard notation, or empty string if error
        """
        if not pgn_string:
            return ''
        
        try:
            pgn = StringIO(pgn_string)
            game = chess.pgn.read_game(pgn)
            
            if game is None:
                return ''
            
            board = game.board()
            moves = []
            move_number = 1
            
            for i, move in enumerate(list(game.mainline_moves())[:12]):
                san_move = board.san(move)
                
                # Add move number before White's move
                if i % 2 == 0:
                    moves.append(f"{move_number}. {san_move}")
                else:
                    moves.append(san_move)
                    move_number += 1
                
                board.push(move)
            
            return ' '.join(moves)
            
        except Exception as e:
            logger.warning(f"Error extracting first 12 moves: {e}")
            return ''
    
    def _get_opening_position_fen(self, pgn_string: str) -> str:
        """
        Get FEN position after first 12 individual moves (6 full moves) from PGN.
        
        Args:
            pgn_string: PGN string from game data
            
        Returns:
            FEN string representing board position after 6 full moves, or empty string if error
        """
        if not pgn_string:
            return ''
        
        try:
            pgn = StringIO(pgn_string)
            game = chess.pgn.read_game(pgn)
            
            if game is None:
                return ''
            
            board = game.board()
            
            # Play first 12 moves (6 full moves)
            for i, move in enumerate(list(game.mainline_moves())[:12]):
                board.push(move)
            
            # Return FEN position
            return board.fen()
            
        except Exception as e:
            logger.warning(f"Error generating FEN: {e}")
            return ''
    
    def _analyze_opponent_strength(self, games: List[Dict]) -> Dict:
        """Analyze performance against opponents of different strengths."""
        categories = {
            'much_lower': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'rating_sum': 0},
            'lower': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'rating_sum': 0},
            'similar': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'rating_sum': 0},
            'higher': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'rating_sum': 0},
            'much_higher': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'rating_sum': 0}
        }
        
        total_opponent_rating = 0
        games_with_rating = 0
        
        for game in games:
            player_rating = game['player_rating']
            opponent_rating = game['opponent_rating']
            
            if not player_rating or not opponent_rating:
                continue
            
            total_opponent_rating += opponent_rating
            games_with_rating += 1
            
            # Calculate Elo differential
            elo_diff = opponent_rating - player_rating
            
            # Categorize with 5 levels
            if elo_diff < -200:
                category = 'much_lower'
            elif -200 <= elo_diff < -100:
                category = 'lower'
            elif -100 <= elo_diff <= 99:
                category = 'similar'
            elif 100 <= elo_diff < 200:
                category = 'higher'
            else:  # >= 200
                category = 'much_higher'
            
            result = game['result']
            categories[category]['games'] += 1
            categories[category]['rating_sum'] += opponent_rating
            
            if result == 'win':
                categories[category]['wins'] += 1
            elif result == 'loss':
                categories[category]['losses'] += 1
            else:  # result == 'draw'
                categories[category]['draws'] += 1
        
        # Calculate win rates and average opponent ratings for each category
        for category in categories.values():
            total = category['games']
            win_rate = (category['wins'] / total * 100) if total > 0 else 0
            category['win_rate'] = round(win_rate, 2)
            
            # Calculate average opponent rating for this category
            avg_opp_rating = (category['rating_sum'] / total) if total > 0 else 0
            category['avg_rating'] = round(avg_opp_rating, 1)
            
            # Remove rating_sum as it's not needed in output
            del category['rating_sum']
        
        avg_opponent_rating = total_opponent_rating / games_with_rating if games_with_rating > 0 else 0
        
        return {
            'avg_opponent_rating': round(avg_opponent_rating, 1),
            'by_rating_diff': categories
        }
    
    def _analyze_time_of_day(self, games: List[Dict]) -> Dict:
        """Analyze performance by time of day."""
        periods = {
            'morning': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'rating_sum': 0},
            'afternoon': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'rating_sum': 0},
            'evening': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'rating_sum': 0},
            'night': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0, 'rating_sum': 0}
        }
        
        for game in games:
            period = game['time_of_day']
            result = game['result']
            player_rating = game['player_rating']
            
            periods[period]['games'] += 1
            if player_rating:
                periods[period]['rating_sum'] += player_rating
            
            if result == 'win':
                periods[period]['wins'] += 1
            elif result == 'loss':
                periods[period]['losses'] += 1
            else:  # result == 'draw'
                periods[period]['draws'] += 1
        
        # Calculate win rates and average ratings
        for period in periods.values():
            total = period['games']
            win_rate = (period['wins'] / total * 100) if total > 0 else 0
            period['win_rate'] = round(win_rate, 2)
            
            # Calculate average rating for this time period
            avg_rating = (period['rating_sum'] / total) if total > 0 else 0
            period['avg_rating'] = round(avg_rating, 1)
            
            # Remove rating_sum as it's not needed in output
            del period['rating_sum']
        
        return periods
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure."""
        return {
            'total_games': 0,
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
            }
        }
