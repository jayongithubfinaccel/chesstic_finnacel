"""
Mistake analysis service using Stockfish engine for game evaluation.
Milestone 8: Game Stage Mistake Analysis
PRD v2.1: Updated critical mistake game link criteria (lost by resignation only)
PRD v2.10 (Iteration 11): Lichess Cloud API integration for 10-20x performance improvement
PRD v2.11 (Iteration 12): Node-limited search + batch FEN evaluation for 1 vCPU optimization
"""
import chess
import chess.engine
import chess.pgn
from io import StringIO
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging
from app.services.lichess_evaluation_service import LichessEvaluationService

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
    
    # Strategic move sampling (Iteration 12: Reduced to 15 moves for 1 vCPU)
    # 5 early + 5 middle + 5 endgame = 15 moves per game
    MOVES_PER_STAGE = 5           # Moves to analyze per stage
    MAX_MOVES_PER_GAME = 15       # Maximum moves to analyze per game (3 stages × 5)
    
    def __init__(self, stockfish_path: str = 'stockfish', engine_depth: int = 10, 
                 time_limit: float = 0.5, engine_nodes: int = 50000, enabled: bool = True, 
                 use_lichess_cloud: bool = True, lichess_timeout: float = 5.0,
                 max_analysis_games: int = 10, moves_per_game: int = 15):
        """
        Initialize mistake analysis service.
        
        Args:
            stockfish_path: Path to Stockfish executable
            engine_depth: Analysis depth (default: 10, used only if engine_nodes=0)
            time_limit: Time limit per position in seconds (default: 0.5s, used only if engine_nodes=0)
            engine_nodes: Node limit for Stockfish (default: 50000, Iteration 12). Set to 0 to use depth/time.
            enabled: Whether engine analysis is enabled
            use_lichess_cloud: Whether to use Lichess Cloud API first (default: True, v2.10)
            lichess_timeout: Timeout for Lichess API calls in seconds (default: 5.0)
            max_analysis_games: Maximum games to analyze (default: 10, Iteration 12)
            moves_per_game: Moves to analyze per game (default: 15, Iteration 12)
        """
        self.stockfish_path = stockfish_path
        self.engine_depth = engine_depth
        self.time_limit = time_limit
        self.engine_nodes = engine_nodes  # Iteration 12: Node-limited search
        self.enabled = enabled
        self.use_lichess_cloud = use_lichess_cloud
        self.max_analysis_games = max_analysis_games  # Iteration 12
        self.moves_per_game = moves_per_game  # Iteration 12
        self.engine = None
        
        # Initialize Lichess Cloud service (Iteration 11)
        self.lichess_service = LichessEvaluationService(timeout=lichess_timeout) if use_lichess_cloud else None
        
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
        Evaluate position using Lichess Cloud API with Stockfish fallback.
        PRD v2.11 (Iteration 12): Added node-limited search for predictable timing on 1 vCPU.
        
        Args:
            board: Chess board position
            
        Returns:
            Evaluation in centipawns (from current player's perspective), or None if error
        """
        # Step 1: Try Lichess Cloud API first (fast path: 0.01-0.05s)
        if self.use_lichess_cloud and self.lichess_service:
            fen = board.fen()
            lichess_eval = self.lichess_service.evaluate_position(fen)
            
            if lichess_eval is not None:
                return lichess_eval  # Fast path succeeded
        
        # Step 2: Fallback to local Stockfish (slow path: 0.2-0.5s)
        # Keep existing Stockfish code as requested - do not remove
        if not self.engine:
            return None
            
        try:
            # Iteration 12: Node-limited search for predictable timing (~0.05-0.1s per position)
            if self.engine_nodes > 0:
                # Node-limited search: 50K nodes = consistent ~0.1s timing
                info = self.engine.analyse(
                    board, 
                    chess.engine.Limit(nodes=self.engine_nodes)
                )
            elif self.use_lichess_cloud:
                # Ultra-fast fallback when Lichess is primary: 100ms hard limit
                info = self.engine.analyse(
                    board, 
                    chess.engine.Limit(time=0.1)  # 100ms hard limit
                )
            else:
                # Traditional mode: use depth with time limit
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
        PRD v2.11 (Iteration 12): 5 early + 5 middle + 5 endgame = 15 moves per game.
        Redistributes unused moves when game is too short.
        
        Args:
            total_player_moves: Total number of player moves in the game
            
        Returns:
            Set of move indices (0-based) to analyze
        """
        moves_to_analyze = set()
        
        # If game has <= 15 moves, analyze all
        if total_player_moves <= self.moves_per_game:
            return set(range(total_player_moves))
        
        # Calculate stage boundaries (early: 0-33%, middle: 33-66%, end: 66-100%)
        early_end = total_player_moves // 3
        middle_end = 2 * total_player_moves // 3
        
        # Early game: First 5 moves (or all if less than 5)
        early_moves = min(self.MOVES_PER_STAGE, early_end)
        early_selected = set(range(early_moves))
        
        # Endgame: Last 5 moves (or all if less than 5 remaining)
        endgame_moves = min(self.MOVES_PER_STAGE, total_player_moves - middle_end)
        endgame_selected = set(range(total_player_moves - endgame_moves, total_player_moves))
        
        # Middle game: Sample 5 moves evenly from middle section
        middle_range = middle_end - early_end
        middle_moves = min(self.MOVES_PER_STAGE, middle_range)
        middle_selected = set()
        
        if middle_moves > 0 and middle_range > 0:
            step = middle_range / middle_moves
            for i in range(middle_moves):
                move_idx = early_end + int(i * step)
                middle_selected.add(move_idx)
        
        # Combine all selections
        moves_to_analyze.update(early_selected)
        moves_to_analyze.update(middle_selected)
        moves_to_analyze.update(endgame_selected)
        
        # Redistribution: If we have fewer than 15 moves, fill from under-sampled stages
        if len(moves_to_analyze) < self.moves_per_game:
            remaining_slots = self.moves_per_game - len(moves_to_analyze)
            
            # Find moves not yet selected
            all_moves = set(range(total_player_moves))
            unselected = all_moves - moves_to_analyze
            
            # Add evenly from unselected moves
            if unselected:
                unselected_list = sorted(unselected)
                step = len(unselected_list) / min(remaining_slots, len(unselected_list))
                for i in range(min(remaining_slots, len(unselected_list))):
                    moves_to_analyze.add(unselected_list[int(i * step)])
        
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
        
        # Iteration 12: Simplified game selection logic
        # Always cap at max_analysis_games (default 10) for consistent performance
        total_games = len(games_data)
        if total_games <= self.max_analysis_games:
            games_to_analyze = games_data  # Analyze all if under limit
        else:
            # Select evenly distributed games up to max limit
            games_to_analyze = self._select_games_for_analysis(games_data, max_games=self.max_analysis_games)
        
        aggregated['sample_info']['analyzed_games'] = len(games_to_analyze)
        if len(games_data) > 0:
            aggregated['sample_info']['sample_percentage'] = round(
                (len(games_to_analyze) / len(games_data)) * 100, 1
            )
        
        logger.info(f"Iteration 12: Analyzing {len(games_to_analyze)} games out of {len(games_data)} total games ({aggregated['sample_info']['sample_percentage']}% sample)")
        
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
            
            # Log Lichess API statistics (Iteration 11)
            if self.use_lichess_cloud and self.lichess_service:
                stats = self.lichess_service.get_stats()
                logger.info(f"Lichess API performance: {stats['hits']} hits, {stats['misses']} misses, "
                          f"{stats['errors']} errors ({stats['hit_rate']:.1f}% hit rate)")
            
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
