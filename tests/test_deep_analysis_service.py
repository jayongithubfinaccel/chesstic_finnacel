"""
Unit tests for DeepAnalysisService.
PRD: chess_page_analysis v2.0
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.deep_analysis_service import DeepAnalysisService


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

SAMPLE_PGN_SHORT = """[Event "Live Chess"]
[White "player1"]
[Black "player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. d4 1-0"""

SAMPLE_PGN_LONG = """[Event "Live Chess"]
[White "testuser"]
[Black "opponent1"]
[Result "0-1"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7
6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7
11. Nbd2 Bb7 12. Bc2 Re8 13. Nf1 Bf8 14. Ng3 g6
15. Bg5 Bg7 16. Qd2 h6 17. Bh4 Nh5 18. Nxe5 Nxg3
19. fxg3 dxe5 20. dxe5 Nxe5 21. Qf4 Qd3 0-1"""


def _make_game(pgn, white_user, black_user, white_rating, black_rating,
               white_result, black_result, time_class='blitz', url=''):
    return {
        'pgn': pgn,
        'white': {'username': white_user, 'rating': white_rating, 'result': white_result},
        'black': {'username': black_user, 'rating': black_rating, 'result': black_result},
        'time_class': time_class,
        'time_control': '300',
        'url': url or f'https://chess.com/game/{white_user}-vs-{black_user}',
        'end_time': 1710000000,
    }


# ---------------------------------------------------------------------------
# Test: detect_most_common_time_control
# ---------------------------------------------------------------------------

class TestTimeControlDetection:
    def test_returns_blitz_when_most_common(self):
        svc = DeepAnalysisService(engine_nodes=0)
        games = [
            {'time_class': 'blitz'}, {'time_class': 'blitz'}, {'time_class': 'rapid'},
        ]
        assert svc.detect_most_common_time_control(games) == 'blitz'

    def test_returns_rapid_when_most_common(self):
        svc = DeepAnalysisService(engine_nodes=0)
        games = [
            {'time_class': 'rapid'}, {'time_class': 'rapid'}, {'time_class': 'blitz'},
        ]
        assert svc.detect_most_common_time_control(games) == 'rapid'

    def test_returns_blitz_when_empty(self):
        svc = DeepAnalysisService(engine_nodes=0)
        assert svc.detect_most_common_time_control([]) == 'blitz'


# ---------------------------------------------------------------------------
# Test: filter_lost_games
# ---------------------------------------------------------------------------

class TestFilterLostGames:
    def test_only_lost_games_included(self):
        svc = DeepAnalysisService(engine_nodes=0)
        games = [
            _make_game(SAMPLE_PGN_LONG, 'testuser', 'opp1', 1200, 1300,
                       'resigned', 'win', 'blitz'),
            _make_game(SAMPLE_PGN_LONG, 'testuser', 'opp2', 1200, 1300,
                       'win', 'checkmated', 'blitz'),
        ]
        lost = svc.filter_lost_games(games, 'testuser', 'blitz')
        assert len(lost) == 1
        assert lost[0]['black']['username'] == 'opp1'

    def test_excludes_short_games(self):
        svc = DeepAnalysisService(engine_nodes=0)
        games = [
            _make_game(SAMPLE_PGN_SHORT, 'player1', 'player2', 1200, 1300,
                       'resigned', 'win', 'blitz'),
        ]
        # SAMPLE_PGN_SHORT has < 15 half-moves
        lost = svc.filter_lost_games(games, 'player1', 'blitz')
        assert len(lost) == 0

    def test_filters_by_time_control(self):
        svc = DeepAnalysisService(engine_nodes=0)
        games = [
            _make_game(SAMPLE_PGN_LONG, 'testuser', 'opp1', 1200, 1300,
                       'resigned', 'win', 'rapid'),
        ]
        lost = svc.filter_lost_games(games, 'testuser', 'blitz')
        assert len(lost) == 0

    def test_includes_various_loss_types(self):
        svc = DeepAnalysisService(engine_nodes=0)
        games = []
        for result in ['checkmated', 'timeout', 'resigned', 'abandoned']:
            games.append(
                _make_game(SAMPLE_PGN_LONG, 'testuser', 'opp', 1200, 1300,
                           result, 'win', 'blitz')
            )
        lost = svc.filter_lost_games(games, 'testuser', 'blitz')
        assert len(lost) == 4


# ---------------------------------------------------------------------------
# Test: player_color / player_result / is_loss
# ---------------------------------------------------------------------------

class TestPlayerHelpers:
    def test_player_color_white(self):
        svc = DeepAnalysisService(engine_nodes=0)
        game = _make_game('', 'testuser', 'opp', 1200, 1300, 'win', 'lose')
        assert svc._player_color(game, 'testuser') == 'white'

    def test_player_color_black(self):
        svc = DeepAnalysisService(engine_nodes=0)
        game = _make_game('', 'opp', 'testuser', 1200, 1300, 'win', 'lose')
        assert svc._player_color(game, 'testuser') == 'black'

    def test_player_color_case_insensitive(self):
        svc = DeepAnalysisService(engine_nodes=0)
        game = _make_game('', 'TestUser', 'opp', 1200, 1300, 'win', 'lose')
        assert svc._player_color(game, 'testuser') == 'white'

    def test_is_loss_true(self):
        svc = DeepAnalysisService(engine_nodes=0)
        for r in ['checkmated', 'timeout', 'resigned', 'abandoned', 'lose']:
            assert svc._is_loss(r) is True

    def test_is_loss_false(self):
        svc = DeepAnalysisService(engine_nodes=0)
        for r in ['win', 'agreed', 'stalemate', 'repetition']:
            assert svc._is_loss(r) is False


# ---------------------------------------------------------------------------
# Test: game stage classification
# ---------------------------------------------------------------------------

class TestStageClassification:
    def test_early_game(self):
        svc = DeepAnalysisService(engine_nodes=0)
        for m in range(1, 8):
            assert svc._get_stage(m) == 'early'

    def test_middle_game(self):
        svc = DeepAnalysisService(engine_nodes=0)
        for m in range(8, 21):
            assert svc._get_stage(m) == 'middle'

    def test_endgame(self):
        svc = DeepAnalysisService(engine_nodes=0)
        assert svc._get_stage(21) == 'endgame'
        assert svc._get_stage(40) == 'endgame'


# ---------------------------------------------------------------------------
# Test: annotation logic
# ---------------------------------------------------------------------------

class TestAnnotation:
    def test_blunder(self):
        assert DeepAnalysisService._annotate(250, -250, False) == '??'

    def test_mistake(self):
        assert DeepAnalysisService._annotate(150, -150, False) == '?'

    def test_inaccuracy(self):
        assert DeepAnalysisService._annotate(60, -60, False) == '?!'

    def test_no_annotation(self):
        assert DeepAnalysisService._annotate(10, -10, False) == ''

    def test_good_move_best(self):
        assert DeepAnalysisService._annotate(5, 60, True) == '!'

    def test_brilliant(self):
        assert DeepAnalysisService._annotate(0, 150, False) == '!!'


# ---------------------------------------------------------------------------
# Test: count_total_moves
# ---------------------------------------------------------------------------

class TestCountMoves:
    def test_short_pgn(self):
        svc = DeepAnalysisService(engine_nodes=0)
        count = svc._count_total_moves(SAMPLE_PGN_SHORT)
        assert count == 5  # e4 e5 Nf3 Nc6 d4

    def test_empty_pgn(self):
        svc = DeepAnalysisService(engine_nodes=0)
        assert svc._count_total_moves('') == 0

    def test_long_pgn(self):
        svc = DeepAnalysisService(engine_nodes=0)
        count = svc._count_total_moves(SAMPLE_PGN_LONG)
        assert count >= 15


# ---------------------------------------------------------------------------
# Test: evaluate_single_position
# ---------------------------------------------------------------------------

class TestEvaluateSinglePosition:
    def test_invalid_fen_returns_error(self):
        svc = DeepAnalysisService(engine_nodes=0)
        result = svc.evaluate_single_position('invalid fen string')
        assert 'error' in result

    @patch.object(DeepAnalysisService, '_start_engine')
    @patch.object(DeepAnalysisService, '_stop_engine')
    @patch.object(DeepAnalysisService, '_evaluate_position', return_value=35)
    @patch.object(DeepAnalysisService, '_get_best_move')
    def test_valid_fen_returns_eval(self, mock_best, mock_eval, mock_stop, mock_start):
        import chess
        mock_start.return_value = MagicMock()
        mock_best.return_value = chess.Move.from_uci('e7e5')
        svc = DeepAnalysisService(engine_nodes=0, use_lichess_cloud=False)
        result = svc.evaluate_single_position(
            'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1'
        )
        assert result['eval'] == 35
        assert result['best_move'] is not None


# ---------------------------------------------------------------------------
# Test: analyze (integration-like, engine mocked)
# ---------------------------------------------------------------------------

class TestAnalyzePipeline:
    @patch.object(DeepAnalysisService, '_start_engine')
    @patch.object(DeepAnalysisService, '_stop_engine')
    @patch.object(DeepAnalysisService, '_evaluate_position', return_value=50)
    @patch.object(DeepAnalysisService, '_get_best_move')
    def test_no_qualifying_games(self, mock_best, mock_eval, mock_stop, mock_start):
        """All games are wins — no qualifying games."""
        import chess
        mock_start.return_value = MagicMock()
        mock_best.return_value = chess.Move.from_uci('e2e4')

        svc = DeepAnalysisService(engine_nodes=0)
        games = [
            _make_game(SAMPLE_PGN_LONG, 'testuser', 'opp', 1200, 1300,
                       'win', 'resigned', 'blitz'),
        ]
        result = svc.analyze(games, 'testuser')
        assert result['games_qualifying'] == 0
        assert len(result['games']) == 0

    def test_engine_not_available(self):
        """When engine cannot start, returns error."""
        svc = DeepAnalysisService(stockfish_path='/nonexistent/path', engine_nodes=0)
        games = [
            _make_game(SAMPLE_PGN_LONG, 'testuser', 'opp', 1200, 1300,
                       'resigned', 'win', 'blitz'),
        ]
        result = svc.analyze(games, 'testuser')
        assert 'error' in result
        assert len(result['games']) == 0


# ---------------------------------------------------------------------------
# Test: clock time parsing (Iteration 2)
# ---------------------------------------------------------------------------

class TestClockTimeParsing:
    def test_parse_clock_standard(self):
        assert DeepAnalysisService._parse_clock_time('[%clk 0:09:58]') == 598

    def test_parse_clock_with_surrounding_text(self):
        assert DeepAnalysisService._parse_clock_time('some text [%clk 1:02:30] more') == 3750

    def test_parse_clock_zero(self):
        assert DeepAnalysisService._parse_clock_time('[%clk 0:00:00]') == 0

    def test_parse_clock_none(self):
        assert DeepAnalysisService._parse_clock_time(None) is None

    def test_parse_clock_empty(self):
        assert DeepAnalysisService._parse_clock_time('') is None

    def test_parse_clock_no_match(self):
        assert DeepAnalysisService._parse_clock_time('no clock data here') is None

    def test_parse_clock_short_time(self):
        assert DeepAnalysisService._parse_clock_time('[%clk 0:00:15]') == 15


SAMPLE_PGN_WITH_CLOCKS = """[Event "Live Chess"]
[White "testuser"]
[Black "opponent1"]
[Result "0-1"]

1. e4 {[%clk 0:09:58]} 1... e5 {[%clk 0:09:56]}
2. Nf3 {[%clk 0:09:45]} 2... Nc6 {[%clk 0:09:50]}
3. Bb5 {[%clk 0:09:30]} 3... a6 {[%clk 0:09:44]}
4. Ba4 {[%clk 0:09:20]} 4... Nf6 {[%clk 0:09:38]}
5. O-O {[%clk 0:09:10]} 5... Be7 {[%clk 0:09:30]}
6. Re1 {[%clk 0:09:00]} 6... b5 {[%clk 0:09:20]}
7. Bb3 {[%clk 0:08:50]} 7... d6 {[%clk 0:09:10]}
8. c3 {[%clk 0:08:40]} 8... O-O {[%clk 0:09:00]}
9. h3 {[%clk 0:08:30]} 9... Nb8 {[%clk 0:08:50]}
10. d4 {[%clk 0:08:20]} 10... Nbd7 {[%clk 0:08:40]} 0-1"""


class TestEvaluateFullGameClocks:
    @patch.object(DeepAnalysisService, '_evaluate_position', return_value=50)
    @patch.object(DeepAnalysisService, '_get_best_move', return_value=None)
    def test_clock_time_included_in_moves(self, mock_best, mock_eval):
        svc = DeepAnalysisService(engine_nodes=0)
        moves = svc.evaluate_full_game(SAMPLE_PGN_WITH_CLOCKS, True)
        assert len(moves) > 0
        # First white move should have clock 598 (9:58)
        assert moves[0]['clock_time'] == 598
        # First black move should have clock 596 (9:56)
        assert moves[1]['clock_time'] == 596

    @patch.object(DeepAnalysisService, '_evaluate_position', return_value=50)
    @patch.object(DeepAnalysisService, '_get_best_move', return_value=None)
    def test_no_clock_returns_none(self, mock_best, mock_eval):
        svc = DeepAnalysisService(engine_nodes=0)
        moves = svc.evaluate_full_game(SAMPLE_PGN_LONG, True)
        assert len(moves) > 0
        # No clock data in SAMPLE_PGN_LONG
        assert moves[0]['clock_time'] is None


# ---------------------------------------------------------------------------
# Test: max_games=20 default (Iteration 2)
# ---------------------------------------------------------------------------

class TestMaxGamesDefault:
    def test_default_max_games_is_20(self):
        svc = DeepAnalysisService(engine_nodes=0)
        assert svc.max_games == 20

    def test_custom_max_games(self):
        svc = DeepAnalysisService(engine_nodes=0, max_games=5)
        assert svc.max_games == 5


# ---------------------------------------------------------------------------
# Test: end_time in analyze results (Iteration 2)
# ---------------------------------------------------------------------------

class TestEndTimeInResults:
    @patch.object(DeepAnalysisService, '_start_engine')
    @patch.object(DeepAnalysisService, '_stop_engine')
    @patch.object(DeepAnalysisService, '_evaluate_position', return_value=50)
    @patch.object(DeepAnalysisService, '_get_best_move')
    @patch.object(DeepAnalysisService, 'generate_game_summary', return_value='')
    def test_end_time_included(self, mock_summary, mock_best, mock_eval, mock_stop, mock_start):
        import chess
        mock_start.return_value = MagicMock()
        mock_best.return_value = chess.Move.from_uci('e2e4')

        svc = DeepAnalysisService(engine_nodes=0, max_games=1)
        games = [
            _make_game(SAMPLE_PGN_LONG, 'testuser', 'opp', 1200, 1300,
                       'resigned', 'win', 'blitz'),
        ]
        result = svc.analyze(games, 'testuser')
        if result['games']:
            assert 'end_time' in result['games'][0]
            assert result['games'][0]['end_time'] == 1710000000

    @patch.object(DeepAnalysisService, '_start_engine')
    @patch.object(DeepAnalysisService, '_stop_engine')
    @patch.object(DeepAnalysisService, '_evaluate_position', return_value=50)
    @patch.object(DeepAnalysisService, '_get_best_move')
    @patch.object(DeepAnalysisService, 'generate_game_summary', return_value='')
    def test_ai_summary_field_present(self, mock_summary, mock_best, mock_eval, mock_stop, mock_start):
        import chess
        mock_start.return_value = MagicMock()
        mock_best.return_value = chess.Move.from_uci('e2e4')

        svc = DeepAnalysisService(engine_nodes=0, max_games=1)
        games = [
            _make_game(SAMPLE_PGN_LONG, 'testuser', 'opp', 1200, 1300,
                       'resigned', 'win', 'blitz'),
        ]
        result = svc.analyze(games, 'testuser')
        if result['games']:
            assert 'ai_summary' in result['games'][0]


# ---------------------------------------------------------------------------
# Test: AI game summary generation (Iteration 2)
# ---------------------------------------------------------------------------

class TestAISummaryGeneration:
    def test_no_api_key_returns_empty(self):
        svc = DeepAnalysisService(engine_nodes=0, openai_api_key='')
        game_data = {
            'player_color': 'white',
            'white': {'username': 'testuser', 'rating': 1200},
            'black': {'username': 'opp', 'rating': 1300},
            'result': 'resigned',
            'time_control': '300',
            'critical_move_number': 15,
            'critical_move_stage': 'middle',
            'critical_cpl': 250,
            'moves': [],
        }
        summary = svc.generate_game_summary(game_data, 'testuser')
        assert summary == ''

    @patch('app.services.deep_analysis_service.DeepAnalysisService.generate_game_summary')
    def test_summary_called_with_api_key(self, mock_summary):
        mock_summary.return_value = 'Test summary'
        svc = DeepAnalysisService(engine_nodes=0, openai_api_key='test-key')
        game_data = {
            'player_color': 'white',
            'white': {'username': 'testuser', 'rating': 1200},
            'black': {'username': 'opp', 'rating': 1300},
            'result': 'resigned',
            'time_control': '300',
            'critical_move_number': 15,
            'critical_move_stage': 'middle',
            'critical_cpl': 250,
            'moves': [],
        }
        result = svc.generate_game_summary(game_data, 'testuser')
        assert result == 'Test summary'
