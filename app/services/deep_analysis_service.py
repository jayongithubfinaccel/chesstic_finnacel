"""
Deep Analysis Service for multi-board game review.
PRD: chess_page_analysis v2.0
Selects lost games with middle/endgame errors, evaluates every move,
and returns full analysis data for the interactive single-column UI.
Includes clock time parsing, AI game summary generation, and game timestamps.
"""
import chess
import chess.engine
import chess.pgn
import re
from io import StringIO
from typing import Dict, List, Optional, Tuple
from collections import Counter
import logging

from app.services.lichess_evaluation_service import LichessEvaluationService

logger = logging.getLogger(__name__)


class DeepAnalysisService:
    """Service for deep game analysis with full move-by-move evaluation."""

    # Game stage thresholds (per-player move numbers, matching MistakeAnalysisService)
    EARLY_GAME_END = 7
    MIDDLE_GAME_END = 20

    # Minimum total moves (half-moves) to consider a game
    MIN_GAME_MOVES = 15

    # CPL thresholds
    INACCURACY_THRESHOLD = 50
    MISTAKE_THRESHOLD = 100
    BLUNDER_THRESHOLD = 200

    # Loss result codes from Chess.com API
    LOSS_RESULTS = {'checkmated', 'timeout', 'resigned', 'abandoned', 'lose'}

    def __init__(
        self,
        stockfish_path: str = 'stockfish',
        engine_nodes: int = 50000,
        engine_depth: int = 10,
        engine_time_limit: float = 0.5,
        use_lichess_cloud: bool = False,
        lichess_timeout: float = 5.0,
        max_games: int = 20,
        openai_api_key: str = '',
        openai_model: str = 'gpt-4o-mini',
    ):
        self.stockfish_path = stockfish_path
        self.engine_nodes = engine_nodes
        self.engine_depth = engine_depth
        self.engine_time_limit = engine_time_limit
        self.use_lichess_cloud = use_lichess_cloud
        self.max_games = max_games
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.lichess_service = (
            LichessEvaluationService(timeout=lichess_timeout)
            if use_lichess_cloud
            else None
        )

    # ------------------------------------------------------------------
    # Engine lifecycle
    # ------------------------------------------------------------------

    def _start_engine(self) -> Optional[chess.engine.SimpleEngine]:
        try:
            engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            logger.info(f"Stockfish engine started: {self.stockfish_path}")
            return engine
        except Exception as e:
            logger.error(f"Failed to start Stockfish engine: {e}")
            return None

    def _stop_engine(self):
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass
            finally:
                self.engine = None

    # ------------------------------------------------------------------
    # Evaluation helpers
    # ------------------------------------------------------------------

    def _evaluate_position(self, board: chess.Board) -> Optional[int]:
        """Evaluate position. Returns centipawns relative to side-to-move."""
        if self.use_lichess_cloud and self.lichess_service:
            fen = board.fen()
            result = self.lichess_service.evaluate_position(fen)
            if result is not None:
                return result

        if not self.engine:
            return None

        try:
            if self.engine_nodes > 0:
                info = self.engine.analyse(board, chess.engine.Limit(nodes=self.engine_nodes))
            else:
                info = self.engine.analyse(
                    board,
                    chess.engine.Limit(depth=self.engine_depth, time=self.engine_time_limit),
                )
            score = info.get('score')
            if score:
                cp = score.relative.score(mate_score=10000)
                return cp if cp is not None else 0
        except Exception as e:
            logger.error(f"Engine analysis error: {e}")
        return None

    def _get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get the engine's best move for the current position."""
        if not self.engine:
            return None
        try:
            if self.engine_nodes > 0:
                result = self.engine.play(board, chess.engine.Limit(nodes=self.engine_nodes))
            else:
                result = self.engine.play(
                    board,
                    chess.engine.Limit(depth=self.engine_depth, time=self.engine_time_limit),
                )
            return result.move
        except Exception as e:
            logger.error(f"Engine best-move error: {e}")
            return None

    def _get_stage(self, move_number: int) -> str:
        if move_number <= self.EARLY_GAME_END:
            return 'early'
        elif move_number <= self.MIDDLE_GAME_END:
            return 'middle'
        return 'endgame'

    @staticmethod
    def _parse_clock_time(comment: str) -> Optional[int]:
        """Parse %clk annotation from a PGN node comment. Returns seconds remaining or None."""
        if not comment:
            return None
        match = re.search(r'\[%clk\s+(\d+):(\d+):(\d+)', comment)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return h * 3600 + m * 60 + s
        return None

    @staticmethod
    def _annotate(cpl: int, cp_change: int, is_best: bool) -> str:
        """Return annotation symbol for a move."""
        if cp_change >= 100 and not is_best:
            # Position improved dramatically from a non-best-move scenario
            return '!!'
        if cp_change >= 50 and is_best:
            return '!'
        if cpl >= 200:
            return '??'
        if cpl >= 100:
            return '?'
        if cpl >= 50:
            return '?!'
        if is_best and cpl < 10:
            return '!'
        return ''

    # ------------------------------------------------------------------
    # Game selection
    # ------------------------------------------------------------------

    def detect_most_common_time_control(self, games: List[Dict]) -> str:
        """Return the most common time_class among games."""
        counter: Counter = Counter()
        for g in games:
            tc = g.get('time_class', 'unknown')
            counter[tc] += 1
        if not counter:
            return 'blitz'
        return counter.most_common(1)[0][0]

    def _player_color(self, game: Dict, username: str) -> Optional[str]:
        """Determine player's color in a game."""
        white_user = game.get('white', {}).get('username', '').lower()
        black_user = game.get('black', {}).get('username', '').lower()
        uname = username.lower()
        if white_user == uname:
            return 'white'
        if black_user == uname:
            return 'black'
        return None

    def _player_result(self, game: Dict, color: str) -> str:
        """Get the player's result string from the game."""
        return game.get(color, {}).get('result', '')

    def _is_loss(self, result: str) -> bool:
        return result.lower() in self.LOSS_RESULTS

    def _count_total_moves(self, pgn_string: str) -> int:
        """Count total half-moves in a PGN."""
        if not pgn_string:
            return 0
        try:
            game = chess.pgn.read_game(StringIO(pgn_string))
            if not game:
                return 0
            return sum(1 for _ in game.mainline_moves())
        except Exception:
            return 0

    def filter_lost_games(
        self, games: List[Dict], username: str, time_control: str
    ) -> List[Dict]:
        """Filter to lost games in the given time control with enough moves."""
        result = []
        for g in games:
            if g.get('time_class', '') != time_control:
                continue
            color = self._player_color(g, username)
            if not color:
                continue
            player_result = self._player_result(g, color)
            if not self._is_loss(player_result):
                continue
            pgn = g.get('pgn', '')
            if self._count_total_moves(pgn) < self.MIN_GAME_MOVES:
                continue
            result.append(g)
        return result

    # ------------------------------------------------------------------
    # Quick scan: find critical mistake per game (middle/endgame only)
    # ------------------------------------------------------------------

    def _find_critical_mistake(
        self, pgn_string: str, player_is_white: bool
    ) -> Tuple[Optional[int], Optional[str], Optional[int]]:
        """
        Scan a game for the largest CPL in middle/endgame.
        Returns (move_number, stage, cpl) or (None, None, None).
        """
        try:
            game = chess.pgn.read_game(StringIO(pgn_string))
            if not game:
                return None, None, None

            board = game.board()
            worst_cpl = 0
            worst_move_num = None
            worst_stage = None
            ply = 0

            for move in game.mainline_moves():
                ply += 1
                move_number = (ply + 1) // 2
                is_player = (board.turn == chess.WHITE) == player_is_white
                stage = self._get_stage(move_number)

                if is_player and stage in ('middle', 'endgame'):
                    eval_before = self._evaluate_position(board)
                    board.push(move)
                    eval_after_opp = self._evaluate_position(board)
                    if eval_before is not None and eval_after_opp is not None:
                        eval_after = -eval_after_opp
                        cpl = max(0, eval_before - eval_after)
                        if cpl > worst_cpl:
                            worst_cpl = cpl
                            worst_move_num = move_number
                            worst_stage = stage
                else:
                    board.push(move)

            if worst_cpl >= self.MISTAKE_THRESHOLD:
                return worst_move_num, worst_stage, worst_cpl
            return None, None, None
        except Exception as e:
            logger.error(f"Error scanning game for critical mistake: {e}")
            return None, None, None

    # ------------------------------------------------------------------
    # Full game evaluation
    # ------------------------------------------------------------------

    def evaluate_full_game(
        self, pgn_string: str, player_is_white: bool
    ) -> List[Dict]:
        """Evaluate every move in a game, returning move-by-move data including clock times."""
        moves_data: List[Dict] = []
        try:
            game = chess.pgn.read_game(StringIO(pgn_string))
            if not game:
                return moves_data

            board = game.board()
            ply = 0
            prev_eval = self._evaluate_position(board)

            node = game
            while node.variations:
                next_node = node.variation(0)
                move = next_node.move
                ply += 1
                move_number = (ply + 1) // 2
                color = 'white' if board.turn == chess.WHITE else 'black'
                is_player = (board.turn == chess.WHITE) == player_is_white
                stage = self._get_stage(move_number)

                fen_before = board.fen()
                san = board.san(move)
                uci = move.uci()

                # Parse clock time from node comment
                clock_time = self._parse_clock_time(next_node.comment)

                # Eval before from the side-to-move perspective
                eval_before = prev_eval if prev_eval is not None else 0

                # Best move at this position
                best_move_obj = self._get_best_move(board)
                best_san = board.san(best_move_obj) if best_move_obj else san
                best_uci = best_move_obj.uci() if best_move_obj else uci
                is_best = (best_move_obj == move) if best_move_obj else True

                board.push(move)
                fen_after = board.fen()

                # Eval after from new side-to-move, negate to keep same perspective
                raw_after = self._evaluate_position(board)
                eval_after = -raw_after if raw_after is not None else eval_before

                # CPL only meaningful for the player
                if is_player:
                    cpl = max(0, eval_before - eval_after)
                    cp_change = eval_after - eval_before
                else:
                    cpl = 0
                    cp_change = 0

                annotation = self._annotate(cpl, cp_change, is_best) if is_player else ''

                moves_data.append({
                    'move_number': move_number,
                    'color': color,
                    'san': san,
                    'uci': uci,
                    'fen_before': fen_before,
                    'fen_after': fen_after,
                    'eval_before': eval_before,
                    'eval_after': eval_after,
                    'cpl': cpl,
                    'best_move_san': best_san,
                    'best_move_uci': best_uci,
                    'annotation': annotation,
                    'stage': stage,
                    'is_player': is_player,
                    'clock_time': clock_time,
                })

                # Update prev eval for next iteration (from next side-to-move)
                prev_eval = raw_after
                node = next_node

        except Exception as e:
            logger.error(f"Error in full game evaluation: {e}")

        return moves_data

    # ------------------------------------------------------------------
    # AI game summary
    # ------------------------------------------------------------------

    def generate_game_summary(self, game_data: Dict, username: str) -> str:
        """Generate an AI narrative summary for a game using OpenAI."""
        if not self.openai_api_key:
            return ''
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)

            color = game_data['player_color']
            opp_color = 'black' if color == 'white' else 'white'
            player_info = game_data[color]
            opp_info = game_data[opp_color]

            # Build eval summary from moves data
            moves = game_data.get('moves', [])
            crit_ply = None
            crit_played = ''
            crit_best = ''
            for i, m in enumerate(moves):
                if m['move_number'] == game_data.get('critical_move_number') and m['color'] == color:
                    crit_ply = i
                    crit_played = m['san']
                    crit_best = m['best_move_san']
                    break

            # Key eval swing points
            eval_swings = []
            for m in moves:
                if m['is_player'] and m['cpl'] >= 50:
                    eval_swings.append(f"Move {m['move_number']}: {m['san']} (CPL {m['cpl']})")
            eval_summary = '; '.join(eval_swings[:5]) if eval_swings else 'No major swings'

            prompt = (
                f"You are a chess analyst. Summarize this game in 3-5 sentences for a player reviewing their loss. "
                f"Describe the flow of the game, the critical mistake, and its consequence. Do not give improvement tips.\n\n"
                f"Player: {username} ({color}, {player_info.get('rating', '?')})\n"
                f"Opponent: {opp_info.get('username', 'Unknown')} ({opp_info.get('rating', '?')})\n"
                f"Result: {game_data.get('result', 'lost')}\n"
                f"Time control: {game_data.get('time_control', '?')}\n"
                f"Critical mistake: Move {game_data.get('critical_move_number', '?')} "
                f"({game_data.get('critical_move_stage', '?')}) - played {crit_played} instead of {crit_best}\n"
                f"CPL at critical move: {game_data.get('critical_cpl', '?')}\n"
                f"Key evaluation changes: {eval_summary}"
            )

            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=300,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed to generate AI game summary: {e}")
            return ''

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def analyze(
        self,
        games: List[Dict],
        username: str,
        progress_callback=None,
    ) -> Dict:
        """
        Run the complete deep analysis pipeline.
        1. Detect most common time control
        2. Filter lost games
        3. Find critical mistakes (quick scan)
        4. Select top N games
        5. Full evaluation of selected games
        Returns a dict ready to be serialised to JSON.
        """
        time_control = self.detect_most_common_time_control(games)
        lost_games = self.filter_lost_games(games, username, time_control)

        self.engine = self._start_engine()
        if not self.engine:
            return {
                'username': username,
                'time_control': time_control,
                'games_analyzed': 0,
                'games_qualifying': 0,
                'games': [],
                'error': 'Stockfish engine not available',
            }

        try:
            # Phase 1: Quick scan for critical mistakes
            candidates = []
            for idx, g in enumerate(lost_games):
                color = self._player_color(g, username)
                pgn = g.get('pgn', '')
                player_is_white = color == 'white'
                move_num, stage, cpl = self._find_critical_mistake(pgn, player_is_white)
                if move_num is not None:
                    candidates.append({
                        'game': g,
                        'color': color,
                        'critical_move_number': move_num,
                        'critical_move_stage': stage,
                        'critical_cpl': cpl,
                    })
                if progress_callback:
                    progress_callback(idx + 1, len(lost_games) + self.max_games)

            # Sort by critical CPL descending
            candidates.sort(key=lambda c: c['critical_cpl'], reverse=True)
            selected = candidates[: self.max_games]

            # Phase 2: Full evaluation of selected games
            result_games = []
            for idx, cand in enumerate(selected):
                g = cand['game']
                color = cand['color']
                pgn = g.get('pgn', '')
                player_is_white = color == 'white'

                moves_data = self.evaluate_full_game(pgn, player_is_white)

                white_info = g.get('white', {})
                black_info = g.get('black', {})
                player_result = self._player_result(g, color)

                result_games.append({
                    'game_url': g.get('url', ''),
                    'white': {
                        'username': white_info.get('username', 'Unknown'),
                        'rating': white_info.get('rating', 0),
                    },
                    'black': {
                        'username': black_info.get('username', 'Unknown'),
                        'rating': black_info.get('rating', 0),
                    },
                    'player_color': color,
                    'result': player_result,
                    'time_control': g.get('time_control', ''),
                    'end_time': g.get('end_time', None),
                    'pgn': pgn,
                    'total_moves': len(moves_data),
                    'critical_move_number': cand['critical_move_number'],
                    'critical_move_stage': cand['critical_move_stage'],
                    'critical_cpl': cand['critical_cpl'],
                    'moves': moves_data,
                    'ai_summary': '',
                })

                if progress_callback:
                    progress_callback(
                        len(lost_games) + idx + 1,
                        len(lost_games) + self.max_games,
                    )

            # Phase 3: Generate AI summaries (after engine is done)
            self._stop_engine()
            for game_data in result_games:
                summary = self.generate_game_summary(game_data, username)
                game_data['ai_summary'] = summary

            return {
                'username': username,
                'time_control': time_control,
                'games_analyzed': len(lost_games),
                'games_qualifying': len(candidates),
                'games': result_games,
            }

        finally:
            self._stop_engine()

    # ------------------------------------------------------------------
    # Single position evaluation (for explore mode)
    # ------------------------------------------------------------------

    def evaluate_single_position(self, fen: str) -> Dict:
        """
        Evaluate a single FEN position. Used by /api/evaluate-position.
        Returns eval, mate info, and best move.
        """
        try:
            board = chess.Board(fen)
        except (ValueError, TypeError):
            return {'error': 'Invalid FEN'}

        # Try Lichess first
        cp_score = None
        if self.use_lichess_cloud and self.lichess_service:
            cp_score = self.lichess_service.evaluate_position(fen)

        best_move_obj = None
        engine_started_here = False

        if cp_score is None:
            if not self.engine:
                self.engine = self._start_engine()
                engine_started_here = True
            if self.engine:
                cp_score = self._evaluate_position(board)
                best_move_obj = self._get_best_move(board)
                if engine_started_here:
                    self._stop_engine()
        else:
            # We have eval from Lichess but still need best move from Stockfish
            if not self.engine:
                self.engine = self._start_engine()
                engine_started_here = True
            if self.engine:
                best_move_obj = self._get_best_move(board)
                if engine_started_here:
                    self._stop_engine()

        if cp_score is None:
            cp_score = 0

        mate = None
        if abs(cp_score) >= 9900:
            mate = 1 if cp_score > 0 else -1

        best_move_uci = best_move_obj.uci() if best_move_obj else None
        best_move_san = board.san(best_move_obj) if best_move_obj else None

        return {
            'eval': cp_score,
            'mate': mate,
            'best_move': {
                'uci': best_move_uci,
                'san': best_move_san,
            } if best_move_obj else None,
        }
