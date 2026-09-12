"""
Unit tests for the Telegram daily/weekly review feature:
- AnalyticsService._extract_first_n_moves / _analyze_opening_by_prefix_length
- game_review_service.format_review_message

No live Chess.com or Telegram calls are made - all games are fixed sample PGNs.
"""
import pytest

from app.services.analytics_service import AnalyticsService
from app.services.game_review_service import format_review_message


# Both games share the exact same first 4 full moves (Italian Game), then
# diverge from move 5 onward - used to verify that grouping at a shorter
# prefix length merges games that a longer prefix length splits apart.
LONG_GAME_A = (
    '[Event "Live Chess"]\n[Site "Chess.com"]\n[White "testuser"]\n'
    '[Black "opponent1"]\n[Result "1-0"]\n[ECO "C50"]\n[Opening "Italian Game"]\n'
    '[Termination "testuser won by resignation"]\n\n'
    '1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d3 d6 6. O-O O-O 7. Re1 a6 1-0'
)
LONG_GAME_B = (
    '[Event "Live Chess"]\n[Site "Chess.com"]\n[White "testuser"]\n'
    '[Black "opponent3"]\n[Result "1-0"]\n[ECO "C50"]\n[Opening "Italian Game"]\n'
    '[Termination "testuser won by checkmate"]\n\n'
    '1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. Qb3 Qe7 6. O-O d6 7. Re1 O-O 1-0'
)
# Ends (via checkmate) after only 3.5 full moves - too short for any of the
# 4/5/6/7-move prefix groupings.
SHORT_GAME = (
    '[Event "Live Chess"]\n[Site "Chess.com"]\n[White "testuser"]\n'
    '[Black "opponent2"]\n[Result "0-1"]\n'
    '[Termination "opponent2 won by checkmate"]\n\n'
    '1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 0-1'
)


def _make_game(pgn, white_username, black_username, white_result, black_result, end_time):
    return {
        'pgn': pgn,
        'end_time': end_time,
        'white': {'username': white_username, 'rating': 1500, 'result': white_result},
        'black': {'username': black_username, 'rating': 1500, 'result': black_result},
        'time_control': '600',
        'time_class': 'rapid',
        'url': 'https://chess.com/game/1',
    }


GAME_A = _make_game(LONG_GAME_A, 'testuser', 'opponent1', 'win', 'resigned', 1735689600)
GAME_B = _make_game(LONG_GAME_B, 'testuser', 'opponent3', 'win', 'checkmated', 1735776000)
GAME_SHORT = _make_game(SHORT_GAME, 'testuser', 'opponent2', 'checkmated', 'win', 1735862400)


@pytest.fixture
def analytics_service():
    return AnalyticsService(engine_enabled=False, openai_api_key='')


class TestExtractFirstNMoves:
    def test_returns_string_when_game_long_enough(self, analytics_service):
        moves = analytics_service._extract_first_n_moves(LONG_GAME_A, 4)
        assert moves == '1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6'

    def test_returns_none_when_game_too_short(self, analytics_service):
        assert analytics_service._extract_first_n_moves(SHORT_GAME, 4) is None

    def test_returns_none_for_empty_pgn(self, analytics_service):
        assert analytics_service._extract_first_n_moves('', 4) is None


class TestAnalyzeOpeningByPrefixLength:
    def _enriched(self, analytics_service, games):
        return analytics_service._parse_and_enrich_games(games, 'testuser', 'UTC')

    def test_short_games_excluded_from_every_length(self, analytics_service):
        enriched = self._enriched(analytics_service, [GAME_SHORT])
        for n in (4, 5, 6, 7):
            result = analytics_service._analyze_opening_by_prefix_length(enriched, n)
            assert result['white'] == []

    def test_games_merge_at_shorter_prefix_and_split_at_longer(self, analytics_service):
        enriched = self._enriched(analytics_service, [GAME_A, GAME_B])

        at_4 = analytics_service._analyze_opening_by_prefix_length(enriched, 4)
        assert len(at_4['white']) == 1
        assert at_4['white'][0]['games'] == 2
        assert at_4['white'][0]['opening_name'] == 'Italian Game'

        at_5 = analytics_service._analyze_opening_by_prefix_length(enriched, 5)
        assert len(at_5['white']) == 2
        assert all(entry['games'] == 1 for entry in at_5['white'])

    def test_win_loss_draw_counts_per_group(self, analytics_service):
        enriched = self._enriched(analytics_service, [GAME_A, GAME_B])
        at_4 = analytics_service._analyze_opening_by_prefix_length(enriched, 4)
        entry = at_4['white'][0]
        assert entry['wins'] == 2
        assert entry['losses'] == 0
        assert entry['win_rate'] == 100.0


class TestFormatReviewMessage:
    def test_no_games_message(self):
        summary = {
            'username': 'testuser',
            'start_date': '2026-09-11',
            'end_date': '2026-09-11',
            'total_games': 0,
        }
        text = format_review_message(summary, 'Daily Chess Review')
        assert 'No games played' in text
        assert '2026-09-11' in text

    def test_includes_color_termination_and_openings(self):
        summary = {
            'username': 'testuser',
            'start_date': '2026-09-11',
            'end_date': '2026-09-11',
            'total_games': 2,
            'totals': {'wins': 2, 'losses': 0, 'draws': 0},
            'white': {
                'totals': {'wins': 2, 'losses': 0, 'draws': 0},
                'termination_wins': {'total_wins': 2, 'breakdown': {'resignation': 1, 'checkmate': 1}},
                'termination_losses': {'total_losses': 0, 'breakdown': {}},
            },
            'black': {
                'totals': {'wins': 0, 'losses': 0, 'draws': 0},
                'termination_wins': {'total_wins': 0, 'breakdown': {}},
                'termination_losses': {'total_losses': 0, 'breakdown': {}},
            },
            'openings_by_length': {
                4: {'white': [{
                    'moves': '1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6',
                    'opening_name': 'Italian Game',
                    'games': 2, 'wins': 2, 'losses': 0, 'draws': 0, 'win_rate': 100.0,
                }], 'black': []},
                5: {'white': [], 'black': []},
                6: {'white': [], 'black': []},
                7: {'white': [], 'black': []},
            },
        }
        text = format_review_message(summary, 'Daily Chess Review')
        assert 'White' in text
        assert 'Won by: Resignation 1, Checkmate 1' in text
        assert 'Italian Game' in text
        assert 'first 4 moves' in text
        # No black openings for this window - section should be omitted
        assert 'Black — Opening' not in text
