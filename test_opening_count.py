"""
Quick test to verify opening performance returns top 5.
"""
import sys
sys.path.insert(0, '.')

from app.services.analytics_service import AnalyticsService
from app.services.chess_service import ChessService
from datetime import datetime, timedelta

def test_opening_count():
    """Test that opening performance returns top 5 for each color."""
    
    # Initialize services
    analytics_service = AnalyticsService(
        engine_enabled=False,  # Disable engine for speed
        openai_api_key=''  # No AI for this test
    )
    chess_service = ChessService()
    
    # Fetch real data
    username = "jay_fh"
    end_date = datetime(2026, 2, 14)
    start_date = datetime(2026, 2, 7)
    
    print(f"Fetching games for {username} from {start_date.date()} to {end_date.date()}...")
    
    games = chess_service.get_games_by_date_range(
        username=username,
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"Found {len(games)} games")
    
    if not games:
        print("No games found!")
        return
    
    # Analyze opening performance
    result = analytics_service.analyze_detailed(
        games=games,
        username=username,
        timezone='America/New_York',
        include_mistake_analysis=False,
        include_ai_advice=False
    )
    
    opening_performance = result['sections']['opening_performance']
    
    # Check counts
    white_count = len(opening_performance['white'])
    black_count = len(opening_performance['black'])
    
    print(f"\nOpening Performance Analysis:")
    print(f"  White openings: {white_count}")
    print(f"  Black openings: {black_count}")
    
    if white_count <= 5 and black_count <= 5:
        print(f"\n✅ PASS: Both colors have <= 5 openings")
        print(f"\nWhite openings:")
        for i, opening in enumerate(opening_performance['white'], 1):
            print(f"  {i}. {opening['opening']} ({opening['games']} games)")
        print(f"\nBlack openings:")
        for i, opening in enumerate(opening_performance['black'], 1):
            print(f"  {i}. {opening['opening']} ({opening['games']} games)")
        return True
    else:
        print(f"\n❌ FAIL: Expected <= 5 openings per color")
        print(f"  Got: white={white_count}, black={black_count}")
        return False

if __name__ == '__main__':
    success = test_opening_count()
    sys.exit(0 if success else 1)
