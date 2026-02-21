"""
Unit tests for analytics service module.
"""
import pytest
from datetime import datetime
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def analytics_service():
    """Create analytics service instance."""
    return AnalyticsService()


@pytest.fixture
def sample_games():
    """Create sample game data for testing."""
    return [
        {
            'pgn': '[Event "Live Chess"]\n[Site "Chess.com"]\n[White "player1"]\n[Black "testuser"]\n[Result "1-0"]\n[Termination "testuser won by checkmate"]\n\n1. e4 e5 2. Nf3 Nc6',
            'end_time': 1735689600,  # 2025-01-01 00:00 UTC
            'white': {'username': 'player1', 'rating': 1500, 'result': 'lose'},
            'black': {'username': 'testuser', 'rating': 1520, 'result': 'win'},
            'time_control': '600',
            'time_class': 'rapid',
            'url': 'https://chess.com/game/1'
        },
        {
            'pgn': '[Event "Live Chess"]\n[Site "Chess.com"]\n[White "testuser"]\n[Black "player2"]\n[Result "0-1"]\n[Termination "testuser lost on time"]\n\n1. d4 d5 2. c4 e6',
            'end_time': 1735776000,  # 2025-01-02 00:00 UTC
            'white': {'username': 'testuser', 'rating': 1520, 'result': 'timeout'},
            'black': {'username': 'player2', 'rating': 1600, 'result': 'win'},
            'time_control': '180',
            'time_class': 'blitz',
            'url': 'https://chess.com/game/2'
        },
        {
            'pgn': '[Event "Live Chess"]\n[Site "Chess.com"]\n[White "testuser"]\n[Black "player3"]\n[Result "1/2-1/2"]\n[Termination "Game drawn by agreement"]\n\n1. e4 e5 2. Nf3 Nf6',
            'end_time': 1735862400,  # 2025-01-03 00:00 UTC
            'white': {'username': 'testuser', 'rating': 1515, 'result': 'agreed'},
            'black': {'username': 'player3', 'rating': 1510, 'result': 'agreed'},
            'time_control': '600',
            'time_class': 'rapid',
            'url': 'https://chess.com/game/3'
        }
    ]


class TestAnalyticsServiceParsing:
    """Test cases for game parsing and enrichment."""
    
    def test_parse_and_enrich_games(self, analytics_service, sample_games):
        """Test parsing and enriching game data."""
        enriched = analytics_service._parse_and_enrich_games(
            sample_games, 
            'testuser', 
            'UTC'
        )
        
        assert len(enriched) == 3
        assert all('player_color' in game for game in enriched)
        assert all('opening_name' in game for game in enriched)
        assert all('termination' in game for game in enriched)
    
    def test_extract_player_color_white(self, analytics_service, sample_games):
        """Test player color extraction when playing white."""
        enriched = analytics_service._parse_and_enrich_games(
            [sample_games[1]], 
            'testuser', 
            'UTC'
        )
        
        assert enriched[0]['player_color'] == 'white'
    
    def test_extract_player_color_black(self, analytics_service, sample_games):
        """Test player color extraction when playing black."""
        enriched = analytics_service._parse_and_enrich_games(
            [sample_games[0]], 
            'testuser', 
            'UTC'
        )
        
        assert enriched[0]['player_color'] == 'black'
    
    def test_extract_termination_checkmate(self, analytics_service):
        """Test termination extraction for checkmate."""
        game = {
            'pgn': '[Termination "player won by checkmate"]',
            'white': {'username': 'test'},
            'black': {'username': 'other'}
        }
        
        termination = analytics_service._extract_termination(game)
        assert termination == 'checkmate'
    
    def test_extract_termination_timeout(self, analytics_service):
        """Test termination extraction for timeout."""
        game = {
            'pgn': '[Termination "player lost on time"]',
            'white': {'username': 'test'},
            'black': {'username': 'other'}
        }
        
        termination = analytics_service._extract_termination(game)
        assert termination == 'timeout'


class TestAnalyticsServiceOverallPerformance:
    """Test cases for overall performance analysis."""
    
    def test_overall_performance_analysis(self, analytics_service, sample_games):
        """Test overall performance analysis."""
        enriched = analytics_service._parse_and_enrich_games(
            sample_games, 
            'testuser', 
            'UTC'
        )
        result = analytics_service._analyze_overall_performance(enriched)
        
        assert 'daily_stats' in result
        assert len(result['daily_stats']) > 0
    
    def test_empty_games_overall_performance(self, analytics_service):
        """Test overall performance with no games."""
        result = analytics_service._analyze_overall_performance([])
        
        assert result['daily_stats'] == []


class TestAnalyticsServiceColorPerformance:
    """Test cases for color performance analysis."""
    
    def test_color_performance_analysis(self, analytics_service, sample_games):
        """Test color performance analysis."""
        enriched = analytics_service._parse_and_enrich_games(
            sample_games, 
            'testuser', 
            'UTC'
        )
        result = analytics_service._analyze_color_performance(enriched)
        
        assert 'white' in result
        assert 'black' in result
        assert 'win_rate' in result['white']
        assert 'win_rate' in result['black']


class TestAnalyticsServiceEloProgression:
    """Test cases for Elo progression analysis."""
    
    def test_elo_progression_analysis(self, analytics_service, sample_games):
        """Test Elo progression analysis."""
        enriched = analytics_service._parse_and_enrich_games(
            sample_games, 
            'testuser', 
            'UTC'
        )
        result = analytics_service._analyze_elo_progression(enriched)
        
        assert 'data_points' in result
        assert 'rating_change' in result
        assert len(result['data_points']) == 3


class TestAnalyticsServiceTermination:
    """Test cases for termination analysis."""
    
    def test_termination_wins_analysis(self, analytics_service, sample_games):
        """Test termination wins analysis."""
        enriched = analytics_service._parse_and_enrich_games(
            sample_games, 
            'testuser', 
            'UTC'
        )
        result = analytics_service._analyze_termination_wins(enriched)
        
        assert isinstance(result, dict)
        assert 'total_wins' in result
        assert 'breakdown' in result
        assert isinstance(result['breakdown'], dict)
        # Breakdown values are integers (counts), not dicts
        assert all(isinstance(v, int) for v in result['breakdown'].values())
    
    def test_termination_losses_analysis(self, analytics_service, sample_games):
        """Test termination losses analysis."""
        enriched = analytics_service._parse_and_enrich_games(
            sample_games, 
            'testuser', 
            'UTC'
        )
        result = analytics_service._analyze_termination_losses(enriched)
        
        assert isinstance(result, dict)


class TestAnalyticsServiceOpponentStrength:
    """Test cases for opponent strength analysis."""
    
    def test_opponent_strength_analysis(self, analytics_service, sample_games):
        """Test opponent strength categorization."""
        enriched = analytics_service._parse_and_enrich_games(
            sample_games, 
            'testuser', 
            'UTC'
        )
        result = analytics_service._analyze_opponent_strength(enriched)
        
        # Current structure: {'avg_opponent_rating': float, 'by_rating_diff': {...}}
        assert 'avg_opponent_rating' in result
        assert 'by_rating_diff' in result
        
        # Check category keys (without '_rated' suffix)
        categories = result['by_rating_diff']
        assert 'lower' in categories
        assert 'similar' in categories
        assert 'higher' in categories
        assert 'much_lower' in categories
        assert 'much_higher' in categories
        
        # Verify each category has required fields
        for category in categories.values():
            assert 'games' in category
            assert 'wins' in category
            assert 'losses' in category
            assert 'draws' in category
            assert 'win_rate' in category
            assert 'avg_rating' in category


class TestAnalyticsServiceTimeOfDay:
    """Test cases for time of day analysis."""
    
    def test_time_of_day_analysis(self, analytics_service, sample_games):
        """Test time of day categorization."""
        enriched = analytics_service._parse_and_enrich_games(
            sample_games, 
            'testuser', 
            'UTC'
        )
        result = analytics_service._analyze_time_of_day(enriched)
        
        assert 'morning' in result
        assert 'afternoon' in result
        assert 'night' in result
        
        for period in result.values():
            assert 'games' in period
            assert 'wins' in period
            assert 'losses' in period
            assert 'draws' in period
            assert 'win_rate' in period


class TestAnalyticsServiceDetailed:
    """Test cases for detailed analysis."""
    
    def test_detailed_analysis_empty_games(self, analytics_service):
        """Test detailed analysis with empty games list."""
        result = analytics_service.analyze_detailed([], 'testuser', 'UTC')
        
        assert result['total_games'] == 0
        assert 'sections' in result
        assert len(result['sections']) == 8
    
    def test_detailed_analysis_with_games(self, analytics_service, sample_games):
        """Test detailed analysis with sample games."""
        result = analytics_service.analyze_detailed(
            sample_games, 
            'testuser', 
            'America/New_York'
        )
        
        assert result['total_games'] == 3
        assert 'sections' in result
        assert 'overall_performance' in result['sections']
        assert 'color_performance' in result['sections']
        assert 'elo_progression' in result['sections']
        assert 'termination_wins' in result['sections']
        assert 'termination_losses' in result['sections']
        assert 'opening_performance' in result['sections']
        assert 'opponent_strength' in result['sections']
        assert 'time_of_day' in result['sections']
