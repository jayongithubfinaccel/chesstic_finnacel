"""
Mistake analysis service using Stockfish engine for game evaluation.
Milestone 8: Game Stage Mistake Analysis
PRD v2.1: Updated critical mistake game link criteria (lost by resignation only)
"""
import chess
import chess.engine
import chess.pgn
from io import StringIO
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class MistakeAnalysisService:
    """Service for analyzing chess game mistakes using Stockfish engine."""
    
    # Game stage thresholds (in move numbers for each side)
    EARLY_GAME_END = 7      # Moves 1-7 per player
    MIDDLE_GAME_END = 20    # Moves 8-20 per player
    
    # Mistake classification thresholds (centipawns)
    INACCURACY_THRESHOLD = 50
    MISTAKE_THRESHOLD = 100
    BLUNDER_THRESHOLD = 200
    
    # PRD v2.3: Optimized for speed (3-4x faster) with strategic move sampling
    EARLY_STOP_THRESHOLD = 300  # Skip detailed analysis for blunders >300 CP
    SKIP_EVAL_THRESHOLD = 600   # Skip analyzing heavily winning/losing positions
    
    # Strategic move sampling (February 18, 2026)
    FIRST_MOVES_TO_ANALYZE = 10   # Always analyze first 10 moves (opening)
    LAST_MOVES_TO_ANALYZE = 10    # Always analyze last 10 moves (endgame)
    MIDDLE_MOVES_TO_ANALYZE = 10  # Sample 10 moves from middle game
    MAX_MOVES_PER_GAME = 30       # Maximum moves to analyze per game
    
    def __init__(self, stockfish_path: str = 'stockfish', engine_depth: int = 10, 
                 time_limit: float = 0.5, enabled: bool = True):
        """
        Initialize mistake analysis service.
        
        Args:
            stockfish_path: Path to Stockfish executable
            engine_depth: Analysis depth (default: 10, balanced for sampled moves in v2.3)
            time_limit: Time limit per position in seconds (default: 0.5s in v2.3)
            enabled: Whether engine analysis is enabled
        """
        self.stockfish_path = stockfish_path
        self.engine_depth = engine_depth
        self.time_limit = time_limit
        self.enabled = enabled
        self.engine = None
        
    def _start_engine(self) -> Optional[chess.engine.SimpleEngine]:
        """Start Stockfish engine."""
        if not self.enabled:
            return None
            
        try:
            engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            logger.info(f"Stockfish engine started: {self.stockfish_path}")
            return engine
        except Exception as e:
            logger.error(f"Failed to start Stockfish engine: {e}")
            return None
    
    def _stop_engine(self):
        """Stop Stockfish engine."""
        if self.engine:
            try:
                self.engine.quit()
                logger.info("Stockfish engine stopped")
            except Exception as e:
                logger.error(f"Error stopping engine: {e}")
            finally:
                self.engine = None
    
    def _get_stage(self, move_number: int) -> str:
        """
        Determine game stage based on move number.
        
        Args:
            move_number: Full move number (1-based, increments after Black's move)
            
        Returns:
            'early', 'middle', or 'endgame'
        """
        if move_number <= self.EARLY_GAME_END:
            return 'early'
        elif move_number <= self.MIDDLE_GAME_END:
            return 'middle'
        else:
            return 'endgame'
    
    def _classify_mistake(self, cp_loss: int) -> Optional[str]:
        """
        Classify mistake type based on centipawn loss.
        
        Args:
            cp_loss: Centipawn loss (positive value)
            
        Returns:
            'inaccuracy', 'mistake', 'blunder', or None
        """
        if cp_loss >= self.BLUNDER_THRESHOLD:
            return 'blunder'
        elif cp_loss >= self.MISTAKE_THRESHOLD:
            return 'mistake'
        elif cp_loss >= self.INACCURACY_THRESHOLD:
            return 'inaccuracy'
        return None
    
    def _evaluate_position(self, board: chess.Board) -> Optional[int]:
        """
        Evaluate position using Stockfish.
        
        Args:
            board: Chess board position
            
        Returns:
            Evaluation in centipawns (from current player's perspective), or None if error
        """
        if not self.engine:
            return None
            
        try:
            info = self.engine.analyse(
                board, 
                chess.engine.Limit(depth=self.engine_depth, time=self.time_limit)
            )
            score = info.get('score')
            if score:
                # Get score relative to side to move
                cp_score = score.relative.score(mate_score=10000)
                return cp_score if cp_score is not None else 0
        except Exception as e:
            logger.error(f"Engine analysis error: {e}")
        
        return None
    
    def _select_moves_to_analyze(self, total_player_moves: int) -> set:
        """
        Select which move indices to analyze using strategic sampling.
        PRD v2.3: First 10, last 10, middle 10 (max 30 total).
        
        Args:
            total_player_moves: Total number of player moves in the game
            
        Returns:
            Set of move indices (0-based) to analyze
        """
        moves_to_analyze = set()
        
        # If game has <= 30 moves, analyze all
        if total_player_moves <= self.MAX_MOVES_PER_GAME:
            return set(range(total_player_moves))
        
        # First 10 moves (opening)
        first_moves = min(self.FIRST_MOVES_TO_ANALYZE, total_player_moves)
        moves_to_analyze.update(range(first_moves))
        
        # Last 10 moves (endgame)
        last_moves = min(self.LAST_MOVES_TO_ANALYZE, total_player_moves)
        moves_to_analyze.update(range(total_player_moves - last_moves, total_player_moves))
        
        # Middle 10 moves (sample evenly from remaining positions)
        # Exclude first 10 and last 10
        middle_start = self.FIRST_MOVES_TO_ANALYZE
        middle_end = total_player_moves - self.LAST_MOVES_TO_ANALYZE
        middle_range = middle_end - middle_start
        
        if middle_range > 0:
            # Sample evenly across middle game
            moves_to_sample = min(self.MIDDLE_MOVES_TO_ANALYZE, middle_range)
            if moves_to_sample > 0:
                step = middle_range / moves_to_sample
                for i in range(moves_to_sample):
                    move_idx = middle_start + int(i * step)
                    moves_to_analyze.add(move_idx)
        
        return moves_to_analyze
    
    def analyze_game_mistakes(self, pgn_string: str, player_color: str) -> Dict:
        """
        Analyze a single game for move quality across all stages.
        PRD v2.5: Tracks brilliant/neutral/mistake moves (simplified classification).
        PRD v2.3: Uses strategic move sampling (first 10, last 10, middle 10).
        
        Args:
            pgn_string: PGN string of the game
            player_color: 'white' or 'black' - which side to analyze
            
        Returns:
            Dictionary with move quality analysis per stage
        """
        mistakes = {
            'early': {
                'total_moves': 0,
                'inaccuracies': 0,  # Kept for backward compatibility
                'mistakes': 0,  # Kept for backward compatibility
                'blunders': 0,  # Kept for backward compatibility
                'missed_opps': 0,
                'cp_losses': [],
                'worst_mistake': None,
                # v2.5: New move quality tracking
                'brilliant_moves': 0,  # ≥+100 CP gain
                'neutral_moves': 0,  # -49 to +99 CP
                'mistake_moves': 0  # ≤-50 CP loss
            },
            'middle': {
                'total_moves': 0,
                'inaccuracies': 0,
                'mistakes': 0,
                'blunders': 0,
                'missed_opps': 0,
                'cp_losses': [],
                'worst_mistake': None,
                'brilliant_moves': 0,
                'neutral_moves': 0,
                'mistake_moves': 0
            },
            'endgame': {
                'total_moves': 0,
                'inaccuracies': 0,
                'mistakes': 0,
                'blunders': 0,
                'missed_opps': 0,
                'cp_losses': [],
                'worst_mistake': None,
                'brilliant_moves': 0,
                'neutral_moves': 0,
                'mistake_moves': 0
            }
        }
        
        if not self.enabled or not self.engine:
            return mistakes
        
        try:
            # Parse PGN
            game = chess.pgn.read_game(StringIO(pgn_string))
            if not game:
                return mistakes
            
            board = game.board()
            player_is_white = (player_color.lower() == 'white')
            
            # First pass: Count total player moves
            total_player_moves = 0
            for move in game.mainline_moves():
                is_player_move = (board.turn == chess.WHITE and player_is_white) or \
                                 (board.turn == chess.BLACK and not player_is_white)
                if is_player_move:
                    total_player_moves += 1
                board.push(move)
            
            # Determine which moves to analyze
            moves_to_analyze = self._select_moves_to_analyze(total_player_moves)
            
            # Second pass: Analyze selected moves
            board = game.board()
            move_number = 0
            ply = 0  # Half-moves (increments every move)
            player_move_index = 0  # Track player move index (0-based)
            
            for move in game.mainline_moves():
                ply += 1
                
                # Calculate full move number (increments after Black's move)
                move_number = (ply + 1) // 2
                
                # Determine game stage
                stage = self._get_stage(move_number)
                
                # Check if it's the player's move
                is_player_move = (board.turn == chess.WHITE and player_is_white) or \
                                 (board.turn == chess.BLACK and not player_is_white)
                
                if is_player_move:
                    mistakes[stage]['total_moves'] += 1
                    
                    # Check if this move should be analyzed
                    should_analyze = player_move_index in moves_to_analyze
                    
                    if should_analyze:
                        # Get evaluation before move
                        current_eval = self._evaluate_position(board)
                        
                        # PRD v2.3: Skip analyzing heavily winning/losing positions (>600 CP)
                        if current_eval is not None and abs(current_eval) > self.SKIP_EVAL_THRESHOLD:
                            board.push(move)
                            player_move_index += 1
                            continue  # Skip analysis, game already heavily decided
                        
                        # Make the move
                        board.push(move)
                        
                        # Get evaluation after move (from opponent's perspective, so negate)
                        new_eval_opponent = self._evaluate_position(board)
                        new_eval = -new_eval_opponent if new_eval_opponent is not None else None
                    
                        # Calculate centipawn change (positive = gain, negative = loss)
                        if current_eval is not None and new_eval is not None:
                            cp_change = new_eval - current_eval  # Positive if position improved
                            cp_loss = current_eval - new_eval  # Positive if position worsened
                            
                            # PRD v2.5: Classify move quality
                            if cp_change >= 100:
                                # Brilliant move: ≥+100 CP gain
                                mistakes[stage]['brilliant_moves'] += 1
                            elif cp_loss >= 50:
                                # Mistake move: ≥-50 CP loss
                                mistakes[stage]['mistake_moves'] += 1
                                
                                # Also update old tracking for backward compatibility
                                mistake_type = self._classify_mistake(cp_loss)
                                if mistake_type == 'inaccuracy':
                                    mistakes[stage]['inaccuracies'] += 1
                                elif mistake_type == 'mistake':
                                    mistakes[stage]['mistakes'] += 1
                                elif mistake_type == 'blunder':
                                    mistakes[stage]['blunders'] += 1
                                
                                mistakes[stage]['cp_losses'].append(cp_loss)
                                
                                # Track worst mistake
                                if mistakes[stage]['worst_mistake'] is None or \
                                   cp_loss > mistakes[stage]['worst_mistake']['cp_loss']:
                                    mistakes[stage]['worst_mistake'] = {
                                        'move_number': move_number,
                                        'cp_loss': cp_loss,
                                        'type': mistake_type or 'mistake'
                                    }
                            else:
                                # Neutral move: -49 to +99 CP
                                mistakes[stage]['neutral_moves'] += 1
                    else:
                        # Move not selected for analysis, just push it
                        board.push(move)
                    
                    player_move_index += 1
                else:
                    # Opponent's move
                    board.push(move)
            
            return mistakes
            
        except Exception as e:
            logger.error(f"Error analyzing game: {e}")
            return mistakes
    
    def aggregate_mistake_analysis(self, games_data: List[Dict], username: str, progress_callback=None) -> Dict:
        """
        Aggregate mistake analysis across all games.
        PRD v2.2: Analyzes exactly 2 games (evenly distributed across time period) for 1-minute performance target.
        PRD v2.1: Critical mistake links now only show games player lost by resignation.
        
        Args:
            games_data: List of game dictionaries with 'pgn', player info, and game result
            username: Player's username to determine color
            progress_callback: Optional callback function(current, total) to report progress
            
        Returns:
            Aggregated mistake analysis with statistics per stage
        """
        if not self.enabled:
            return self._empty_aggregation()
        
        # Start engine
        self.engine = self._start_engine()
        if not self.engine:
            logger.warning("Engine not available, skipping mistake analysis")
            return self._empty_aggregation()
        
        aggregated = {
            'early': {
                'total_moves': 0,
                'inaccuracies': 0,
                'mistakes': 0,
                'blunders': 0,
                'missed_opps': 0,
                'cp_losses': [],
                'worst_game': None,
                'avg_cp_loss': 0,
                'critical_mistake_game': None,  # PRD v2.1: Separate field for critical games
                # v2.5: New move quality tracking
                'brilliant_moves': 0,
                'neutral_moves': 0,
                'mistake_moves': 0,
                'avg_brilliant_per_game': 0.0,
                'avg_neutral_per_game': 0.0,
                'avg_mistakes_per_game': 0.0
            },
            'middle': {
                'total_moves': 0,
                'inaccuracies': 0,
                'mistakes': 0,
                'blunders': 0,
                'missed_opps': 0,
                'cp_losses': [],
                'worst_game': None,
                'avg_cp_loss': 0,
                'critical_mistake_game': None,
                'brilliant_moves': 0,
                'neutral_moves': 0,
                'mistake_moves': 0,
                'avg_brilliant_per_game': 0.0,
                'avg_neutral_per_game': 0.0,
                'avg_mistakes_per_game': 0.0
            },
            'endgame': {
                'total_moves': 0,
                'inaccuracies': 0,
                'mistakes': 0,
                'blunders': 0,
                'missed_opps': 0,
                'cp_losses': [],
                'worst_game': None,
                'avg_cp_loss': 0,
                'critical_mistake_game': None,
                'brilliant_moves': 0,
                'neutral_moves': 0,
                'mistake_moves': 0,
                'avg_brilliant_per_game': 0.0,
                'avg_neutral_per_game': 0.0,
                'avg_mistakes_per_game': 0.0
            },
            'sample_info': {
                'total_games': len(games_data),
                'analyzed_games': 0,
                'sample_percentage': 0
            }
        }
        
        username_lower = username.lower()
        
        # Iteration 5: Dynamic sampling logic
        # <50 games: Analyze all games
        # ≥50 games: Analyze 20% sample (time-distributed)
        total_games = len(games_data)
        if total_games < 50:
            games_to_analyze = games_data  # Analyze all
        else:
            sample_size = max(1, int(total_games * 0.20))  # 20% of games
            games_to_analyze = self._select_games_for_analysis(games_data, max_games=sample_size)
        
        aggregated['sample_info']['analyzed_games'] = len(games_to_analyze)
        if len(games_data) > 0:
            aggregated['sample_info']['sample_percentage'] = round(
                (len(games_to_analyze) / len(games_data)) * 100, 1
            )
        
        logger.info(f"Iteration 5: Analyzing {len(games_to_analyze)} games out of {len(games_data)} total games ({aggregated['sample_info']['sample_percentage']}% sample)")
        
        try:
            # Analyze selected games
            for idx, game_data in enumerate(games_to_analyze):
                # Determine player color
                white_username = game_data.get('white', {}).get('username', '').lower()
                black_username = game_data.get('black', {}).get('username', '').lower()
                player_color = 'white' if white_username == username_lower else 'black'
                
                # Get game result information
                player_result = None
                termination = None
                
                if player_color == 'white':
                    player_result = game_data.get('white', {}).get('result', '')
                    termination = game_data.get('white', {}).get('termination', '')
                else:
                    player_result = game_data.get('black', {}).get('result', '')
                    termination = game_data.get('black', {}).get('termination', '')
                
                pgn = game_data.get('pgn', '')
                if not pgn:
                    logger.warning(f"Game {idx} missing PGN, skipping")
                    continue
                
                # Analyze game
                try:
                    game_mistakes = self.analyze_game_mistakes(pgn, player_color)
                except Exception as e:
                    logger.error(f"Error analyzing game {idx}: {e}")
                    continue
                
                # Check if game qualifies for critical mistake link (PRD v2.1 criteria)
                # Must meet ALL: player lost + resignation termination + significant CP drop
                # Loss values from Chess.com: 'checkmated', 'timeout', 'resigned', 'abandoned', 'lose'
                is_loss = player_result in ['checkmated', 'timeout', 'resigned', 'abandoned', 'lose']
                is_qualifying_game = (
                    is_loss and 
                    (('resign' in termination.lower()) if termination else False)
                )
                
                # Aggregate results
                for stage in ['early', 'middle', 'endgame']:
                    stage_data = game_mistakes[stage]
                    agg_stage = aggregated[stage]
                    
                    agg_stage['total_moves'] += stage_data['total_moves']
                    agg_stage['inaccuracies'] += stage_data['inaccuracies']
                    agg_stage['mistakes'] += stage_data['mistakes']
                    agg_stage['blunders'] += stage_data['blunders']
                    agg_stage['missed_opps'] += stage_data['missed_opps']
                    agg_stage['cp_losses'].extend(stage_data['cp_losses'])
                    
                    # v2.5: Aggregate new move quality metrics
                    agg_stage['brilliant_moves'] += stage_data.get('brilliant_moves', 0)
                    agg_stage['neutral_moves'] += stage_data.get('neutral_moves', 0)
                    agg_stage['mistake_moves'] += stage_data.get('mistake_moves', 0)
                    
                    # Track worst game for this stage (general tracking)
                    worst_mistake = stage_data.get('worst_mistake')
                    if worst_mistake:
                        if agg_stage['worst_game'] is None or \
                           worst_mistake['cp_loss'] > agg_stage['worst_game']['cp_loss']:
                            agg_stage['worst_game'] = {
                                'game_index': idx,
                                'game_url': game_data.get('url', ''),
                                'cp_loss': worst_mistake['cp_loss'],
                                'move_number': worst_mistake['move_number'],
                                'type': worst_mistake['type']
                            }
                    
                    # Track critical mistake game (PRD v2.1: lost by resignation only)
                    if is_qualifying_game and worst_mistake:
                        cp_loss = worst_mistake['cp_loss']
                        # Check if this is bigger than current critical mistake for this stage
                        if agg_stage['critical_mistake_game'] is None or \
                           cp_loss > agg_stage['critical_mistake_game']['cp_loss']:
                            # Build Chess.com URL with move position parameter
                            base_url = game_data.get('url', '')
                            move_num = worst_mistake['move_number']
                            # Calculate ply number (move after which mistake occurred)
                            ply = move_num * 2 if player_color == 'black' else (move_num * 2 - 1)
                            game_url_with_move = f"{base_url}#{ply}" if base_url else None
                            
                            agg_stage['critical_mistake_game'] = {
                                'game_index': idx,
                                'game_url': game_url_with_move,
                                'cp_loss': cp_loss,
                                'move_number': move_num,
                                'type': worst_mistake['type'],
                                'result': player_result,
                                'termination': termination
                            }
                
                # Log progress every 10 games
                if (idx + 1) % 10 == 0:
                    logger.info(f"Analyzed {idx + 1}/{len(games_to_analyze)} games")
                
                # Report progress to callback if provided
                if progress_callback:
                    progress_callback(idx + 1, len(games_to_analyze))
            
            # Calculate averages and apply significance threshold for critical mistakes
            analyzed_games_count = len(games_to_analyze)
            for stage in ['early', 'middle', 'endgame']:
                cp_losses = aggregated[stage]['cp_losses']
                if cp_losses:
                    aggregated[stage]['avg_cp_loss'] = round(sum(cp_losses) / len(cp_losses), 1)
                    
                    # Calculate significance threshold (PRD v2.1: data-driven threshold)
                    # Use 75th percentile or 300 CP, whichever is higher
                    sorted_losses = sorted(cp_losses)
                    percentile_75_idx = int(len(sorted_losses) * 0.75)
                    threshold = max(sorted_losses[percentile_75_idx] if percentile_75_idx < len(sorted_losses) else 300, 300)
                    
                    # Filter critical mistake if below threshold
                    critical_game = aggregated[stage]['critical_mistake_game']
                    if critical_game and critical_game['cp_loss'] < threshold:
                        logger.info(f"{stage} critical mistake ({critical_game['cp_loss']} CP) below threshold ({threshold} CP)")
                        aggregated[stage]['critical_mistake_game'] = None
                else:
                    aggregated[stage]['avg_cp_loss'] = 0
                
                # v2.5: Calculate per-game averages for move quality
                if analyzed_games_count > 0:
                    aggregated[stage]['avg_brilliant_per_game'] = round(
                        aggregated[stage]['brilliant_moves'] / analyzed_games_count, 1
                    )
                    aggregated[stage]['avg_neutral_per_game'] = round(
                        aggregated[stage]['neutral_moves'] / analyzed_games_count, 1
                    )
                    aggregated[stage]['avg_mistakes_per_game'] = round(
                        aggregated[stage]['mistake_moves'] / analyzed_games_count, 1
                    )
            
            logger.info(f"Mistake analysis complete: {len(games_data)} games analyzed")
            
        except Exception as e:
            logger.error(f"Error in aggregate analysis: {e}")
        finally:
            # Always stop engine
            self._stop_engine()
        
        return aggregated
    
    def _select_games_for_analysis(self, games_data: List[Dict], max_games: int) -> List[Dict]:
        """
        Select games for analysis using time-distributed sampling.
        Iteration 5: Used for ≥50 games scenario with dynamic max_games (20% of total).
        
        Args:
            games_data: List of game dictionaries
            max_games: Number of games to analyze
            
        Returns:
            List of selected games for analysis (time-distributed)
        """
        if not games_data:
            return []
        
        total_games = len(games_data)
        
        # If we have fewer games than max_games, analyze all
        if total_games <= max_games:
            return games_data
        
        # Select games evenly distributed across the list (time-distributed)
        # Games are already sorted by date from Chess.com API
        selected_games = []
        interval = total_games / max_games
        
        for i in range(max_games):
            index = int(i * interval)
            if index < total_games:
                selected_games.append(games_data[index])
        
        return selected_games
    
    def _empty_aggregation(self) -> Dict:
        """Return empty aggregation structure (PRD v2.5: includes move quality metrics)."""
        return {
            'early': {
                'total_moves': 0, 'inaccuracies': 0, 'mistakes': 0, 'blunders': 0,
                'missed_opps': 0, 'cp_losses': [], 'worst_game': None, 'avg_cp_loss': 0,
                'critical_mistake_game': None,
                'brilliant_moves': 0, 'neutral_moves': 0, 'mistake_moves': 0,
                'avg_brilliant_per_game': 0.0, 'avg_neutral_per_game': 0.0, 'avg_mistakes_per_game': 0.0
            },
            'middle': {
                'total_moves': 0, 'inaccuracies': 0, 'mistakes': 0, 'blunders': 0,
                'missed_opps': 0, 'cp_losses': [], 'worst_game': None, 'avg_cp_loss': 0,
                'critical_mistake_game': None,
                'brilliant_moves': 0, 'neutral_moves': 0, 'mistake_moves': 0,
                'avg_brilliant_per_game': 0.0, 'avg_neutral_per_game': 0.0, 'avg_mistakes_per_game': 0.0
            },
            'endgame': {
                'total_moves': 0, 'inaccuracies': 0, 'mistakes': 0, 'blunders': 0,
                'missed_opps': 0, 'cp_losses': [], 'worst_game': None, 'avg_cp_loss': 0,
                'critical_mistake_game': None,
                'brilliant_moves': 0, 'neutral_moves': 0, 'mistake_moves': 0,
                'avg_brilliant_per_game': 0.0, 'avg_neutral_per_game': 0.0, 'avg_mistakes_per_game': 0.0
            },
            'sample_info': {
                'total_games': 0,
                'analyzed_games': 0,
                'sample_percentage': 0
            }
        }
    
    def get_weakest_stage(self, aggregated: Dict) -> Tuple[str, str]:
        """
        Identify weakest game stage.
        
        Args:
            aggregated: Aggregated mistake analysis
            
        Returns:
            Tuple of (stage_name, reason)
        """
        if not self.enabled:
            return ('N/A', 'Engine analysis disabled')
        
        # Calculate mistake rate per stage
        mistake_rates = {}
        for stage in ['early', 'middle', 'endgame']:
            total_moves = aggregated[stage]['total_moves']
            if total_moves > 0:
                total_mistakes = (
                    aggregated[stage]['inaccuracies'] +
                    aggregated[stage]['mistakes'] +
                    aggregated[stage]['blunders']
                )
                mistake_rates[stage] = total_mistakes / total_moves
            else:
                mistake_rates[stage] = 0
        
        # Find stage with highest mistake rate
        if max(mistake_rates.values()) == 0:
            return ('N/A', 'No mistakes detected')
        
        weakest_stage = max(mistake_rates, key=mistake_rates.get)
        stage_display = {
            'early': 'Early game',
            'middle': 'Middlegame',
            'endgame': 'Endgame'
        }
        
        return (
            stage_display.get(weakest_stage, weakest_stage),
            f"Highest mistake rate: {mistake_rates[weakest_stage]:.1%}"
        )
