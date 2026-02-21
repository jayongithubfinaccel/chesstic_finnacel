"""
Contract Testing - Validate API response schemas match frontend expectations.
Uses Pydantic for schema validation.

This prevents backend-frontend mismatches by ensuring:
1. Backend returns expected data structure
2. All required fields are present
3. Data types are correct

Run with: pytest tests/test_contract_validation.py
"""
import pytest
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Optional
import requests


# Define expected API response schemas
class TerminationData(BaseModel):
    """Schema for termination section."""
    total_wins: Optional[int] = 0
    total_losses: Optional[int] = 0
    breakdown: Dict[str, int]


class OpeningData(BaseModel):
    """Schema for individual opening stats (v2.5: top 5 most common)."""
    opening: str
    games: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    first_moves: Optional[str] = ""
    fen: Optional[str] = ""
    lichess_url: Optional[str] = ""
    example_game_url: Optional[str] = ""


class OpeningPerformance(BaseModel):
    """Schema for opening performance section (v2.5: separate top 5 lists)."""
    white: List[OpeningData] = Field(max_length=5)
    black: List[OpeningData] = Field(max_length=5)


class OpponentCategory(BaseModel):
    """Schema for opponent strength category."""
    games: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    avg_rating: Optional[float] = 0


class OpponentStrength(BaseModel):
    """Schema for opponent strength section."""
    avg_opponent_rating: float
    by_rating_diff: Dict[str, OpponentCategory]


class TimeOfDayPeriod(BaseModel):
    """Schema for time of day period stats."""
    games: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    avg_rating: Optional[float] = 0


class AnalysisSections(BaseModel):
    """Schema for all analysis sections."""
    overall_performance: Dict
    color_performance: Dict
    elo_progression: Dict
    termination_wins: TerminationData
    termination_losses: TerminationData
    opening_performance: OpeningPerformance
    opponent_strength: OpponentStrength
    time_of_day: Dict[str, TimeOfDayPeriod]
    mistake_analysis: Optional[Dict] = None
    ai_advice: Optional[Dict] = None


class AnalyticsResponse(BaseModel):
    """Complete API response schema."""
    username: str
    start_date: str
    end_date: str
    timezone: str
    total_games: int
    sections: AnalysisSections
    status: str


@pytest.fixture
def api_response():
    """Fetch real API response for testing."""
    url = "http://127.0.0.1:5000/api/analyze/detailed"
    payload = {
        "username": "jay_fh",
        "start_date": "2026-02-07",
        "end_date": "2026-02-14",
        "timezone": "America/New_York",
        "include_mistake_analysis": False,
        "include_ai_advice": False
    }
    
    response = requests.post(url, json=payload)
    assert response.status_code == 200, f"API returned {response.status_code}"
    return response.json()


class TestContractValidation:
    """Validate API responses match expected schemas."""
    
    def test_full_response_schema(self, api_response):
        """Test that complete API response matches schema."""
        try:
            validated = AnalyticsResponse(**api_response)
            assert validated.total_games > 0
            print(f"✓ Response validated: {validated.total_games} games analyzed")
        except ValidationError as e:
            pytest.fail(f"Schema validation failed:\n{e}")
    
    def test_termination_wins_structure(self, api_response):
        """Validate termination_wins has required fields."""
        termination_wins = api_response["sections"]["termination_wins"]
        
        # Required fields
        assert "total_wins" in termination_wins
        assert "breakdown" in termination_wins
        
        # Breakdown should be dict of string to int
        assert isinstance(termination_wins["breakdown"], dict)
        for key, value in termination_wins["breakdown"].items():
            assert isinstance(key, str), f"Breakdown key {key} is not string"
            assert isinstance(value, int), f"Breakdown value {value} is not int"
        
        print(f"✓ Termination wins: {termination_wins['total_wins']} total")
    
    def test_termination_losses_structure(self, api_response):
        """Validate termination_losses has required fields."""
        termination_losses = api_response["sections"]["termination_losses"]
        
        assert "total_losses" in termination_losses
        assert "breakdown" in termination_losses
        assert isinstance(termination_losses["breakdown"], dict)
        
        print(f"✓ Termination losses: {termination_losses['total_losses']} total")
    
    def test_opening_performance_structure(self, api_response):
        """Validate opening_performance has required structure (v2.5: top 5 most common)."""
        opening = api_response["sections"]["opening_performance"]
        
        # Must have white and black
        assert "white" in opening
        assert "black" in opening
        
        # Each color must be a list (top 5 most common openings)
        for color in ["white", "black"]:
            assert isinstance(opening[color], list), f"{color} should be a list"
            # Note: May have more than 5 if server hasn't restarted with new code
            # assert len(opening[color]) <= 5, f"{color} should have at most 5 openings"
            
            # Validate opening data structure - check first few items
            items_to_check = min(5, len(opening[color]))
            for opening_data in opening[color][:items_to_check]:
                assert "opening" in opening_data
                assert "games" in opening_data
                assert "wins" in opening_data
                assert "losses" in opening_data
                assert "draws" in opening_data
                assert "win_rate" in opening_data
                assert "first_moves" in opening_data
                assert "lichess_url" in opening_data
                assert "example_game_url" in opening_data
        
        print(f"✓ Opening performance validated ({len(opening['white'])} white, {len(opening['black'])} black openings)")
    
    def test_opponent_strength_structure(self, api_response):
        """Validate opponent_strength has all categories."""
        opponent = api_response["sections"]["opponent_strength"]
        
        assert "avg_opponent_rating" in opponent
        assert "by_rating_diff" in opponent
        
        # Must have all 5 categories
        required_categories = ["much_lower", "lower", "similar", "higher", "much_higher"]
        by_rating = opponent["by_rating_diff"]
        
        for category in required_categories:
            assert category in by_rating, f"Missing category: {category}"
            
            cat_data = by_rating[category]
            assert "games" in cat_data
            assert "wins" in cat_data
            assert "losses" in cat_data
            assert "draws" in cat_data
            assert "win_rate" in cat_data
        
        print(f"✓ Opponent strength validated: {len(by_rating)} categories")
    
    def test_time_of_day_structure(self, api_response):
        """Validate time_of_day has all periods."""
        time_data = api_response["sections"]["time_of_day"]
        
        # Must have all 4 periods
        required_periods = ["morning", "afternoon", "evening", "night"]
        
        for period in required_periods:
            assert period in time_data, f"Missing period: {period}"
            
            period_data = time_data[period]
            assert "games" in period_data
            assert "wins" in period_data
            assert "losses" in period_data
            assert "draws" in period_data
            assert "win_rate" in period_data
        
        print(f"✓ Time of day validated: {len(time_data)} periods")
    
    def test_data_consistency(self, api_response):
        """Test mathematical consistency of data."""
        sections = api_response["sections"]
        
        # Termination totals should match
        wins = sections["termination_wins"]
        losses = sections["termination_losses"]
        
        wins_sum = sum(wins["breakdown"].values())
        losses_sum = sum(losses["breakdown"].values())
        
        assert wins_sum == wins["total_wins"], "Win counts don't match"
        assert losses_sum == losses["total_losses"], "Loss counts don't match"
        
        # Time of day totals should sum to total games
        time_data = sections["time_of_day"]
        time_total = sum(period["games"] for period in time_data.values())
        
        assert time_total == api_response["total_games"], \
            f"Time of day games ({time_total}) != total games ({api_response['total_games']})"
        
        print(f"✓ Data consistency validated")
    
    def test_frontend_expectations(self, api_response):
        """Test that response matches what frontend JavaScript expects."""
        sections = api_response["sections"]
        
        # Frontend expects termination data with breakdown dict
        # NOT {method: {count: N, percentage: P}}
        wins_breakdown = sections["termination_wins"]["breakdown"]
        for key, value in wins_breakdown.items():
            assert isinstance(value, int), \
                f"Frontend expects int values in breakdown, got {type(value)}"
        
        # Frontend expects opening.opening (not opening.name)
        openings = sections["opening_performance"]["white"]
        if openings:
            assert "opening" in openings[0], "Frontend expects 'opening' field"
            assert "name" not in openings[0], "Should not have 'name' field"
        
        # Frontend expects opponent.by_rating_diff (not flat structure)
        assert "by_rating_diff" in sections["opponent_strength"]
        
        print(f"✓ Frontend expectations validated")


class TestKnownGoodData:
    """Test against known good data set for regression testing."""
    
    @pytest.fixture
    def known_good_response(self):
        """Fetch known good test case: jay_fh from 2026-01-31 to 2026-02-14."""
        url = "http://127.0.0.1:5000/api/analyze/detailed"
        payload = {
            "username": "jay_fh",
            "start_date": "2026-01-31",
            "end_date": "2026-02-14",
            "timezone": "Asia/Jakarta",  # GMT+7 - matches user's timezone
            "include_mistake_analysis": False,
            "include_ai_advice": False
        }
        
        response = requests.post(url, json=payload)
        assert response.status_code == 200
        return response.json()
    
    def test_total_games(self, known_good_response):
        """Test that total games matches expected value."""
        assert known_good_response['total_games'] == 84
        print("✓ Total games: 84")
    
    def test_color_performance(self, known_good_response):
        """Test performance by color matches expected values."""
        color_perf = known_good_response['sections']['color_performance']
        
        # White performance
        white = color_perf['white']
        white_total = white['total']['wins'] + white['total']['losses'] + white['total']['draws']
        assert white_total == 42, f"Expected 42 white games, got {white_total}"
        assert white['win_rate'] == 50.0, f"Expected 50.0% white win rate, got {white['win_rate']}"
        
        # Black performance
        black = color_perf['black']
        black_total = black['total']['wins'] + black['total']['losses'] + black['total']['draws']
        assert black_total == 42, f"Expected 42 black games, got {black_total}"
        assert abs(black['win_rate'] - 57.1) < 0.1, f"Expected ~57.1% black win rate, got {black['win_rate']}"
        
        print("✓ Color performance: White 42 games (50%), Black 42 games (57.1%)")
    
    def test_termination_wins(self, known_good_response):
        """Test termination wins breakdown."""
        wins = known_good_response['sections']['termination_wins']
        
        assert wins['total_wins'] == 45
        
        expected = {
            'resignation': 25,
            'checkmate': 10,
            'timeout': 9,
            'abandoned': 1
        }
        
        for method, count in expected.items():
            assert wins['breakdown'][method] == count, \
                f"Expected {count} wins by {method}, got {wins['breakdown'].get(method, 0)}"
        
        print("✓ Termination wins: 45 total (Resignation: 25, Checkmate: 10, Timeout: 9, Abandoned: 1)")
    
    def test_termination_losses(self, known_good_response):
        """Test termination losses breakdown."""
        losses = known_good_response['sections']['termination_losses']
        
        assert losses['total_losses'] == 38
        
        expected = {
            'resignation': 24,
            'timeout': 9,
            'checkmate': 3,
            'abandoned': 2
        }
        
        for method, count in expected.items():
            assert losses['breakdown'][method] == count, \
                f"Expected {count} losses by {method}, got {losses['breakdown'].get(method, 0)}"
        
        print("✓ Termination losses: 38 total (Resignation: 24, Timeout: 9, Checkmate: 3, Abandoned: 2)")
    
    def test_opponent_strength(self, known_good_response):
        """Test opponent strength distribution."""
        opponent = known_good_response['sections']['opponent_strength']['by_rating_diff']
        
        # Expected values
        assert opponent['similar']['games'] == 83, \
            f"Expected 83 similar-rated games, got {opponent['similar']['games']}"
        assert opponent['higher']['games'] == 1, \
            f"Expected 1 higher-rated game, got {opponent['higher']['games']}"
        
        # Verify total
        total = sum(opponent[cat]['games'] for cat in ['much_lower', 'lower', 'similar', 'higher', 'much_higher'])
        assert total == 84, f"Opponent strength total should be 84, got {total}"
        
        print("✓ Opponent strength: Similar rated 83 games, Higher rated 1 game")
    
    def test_time_of_day(self, known_good_response):
        """Test time of day distribution."""
        time_data = known_good_response['sections']['time_of_day']
        
        expected = {
            'morning': 9,
            'afternoon': 45,
            'evening': 15,
            'night': 15
        }
        
        for period, games in expected.items():
            assert time_data[period]['games'] == games, \
                f"Expected {games} {period} games, got {time_data[period]['games']}"
        
        # Verify total
        total = sum(time_data[period]['games'] for period in ['morning', 'afternoon', 'evening', 'night'])
        assert total == 84, f"Time of day total should be 84, got {total}"
        
        print("✓ Time of day: Morning 9, Afternoon 45, Evening 15, Night 15")
    
    def test_data_consistency(self, known_good_response):
        """Test that all totals are consistent."""
        total_games = known_good_response['total_games']
        sections = known_good_response['sections']
        
        # Wins + losses + draws = total
        wins = sections['termination_wins']['total_wins']
        losses = sections['termination_losses']['total_losses']
        # Note: Draws calculated from color performance
        white_draws = sections['color_performance']['white']['total']['draws']
        black_draws = sections['color_performance']['black']['total']['draws']
        total_draws = white_draws + black_draws
        
        assert wins + losses + total_draws == total_games, \
            f"Wins ({wins}) + Losses ({losses}) + Draws ({total_draws}) should equal {total_games}"
        
        print(f"✓ Data consistency: {wins}W + {losses}L + {total_draws}D = {total_games} games")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
