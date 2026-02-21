"""
Quick verification script for known test case.
Tests using jay_fh data from 2026-01-31 to 2026-02-14 (84 games).

Run with: uv run python test_quick_verify.py
Ensure Flask server is running first: uv run python run.py
"""
import requests
from typing import Dict


def verify_test_case(timezone="America/New_York", skip_time_check=False):
    """
    Verify the known test case matches expected outputs.
    
    Args:
        timezone: Timezone to use for analysis (default: America/New_York)
        skip_time_check: Skip time of day validation (useful when timezone differs)
    """
    
    print("🔍 Verifying test case: jay_fh (2026-01-31 to 2026-02-14)")
    print(f"   Timezone: {timezone}")
    if skip_time_check:
        print("   ⚠️  Time of Day validation SKIPPED (timezone-dependent)")
    print("=" * 60)
    
    # Make API request
    try:
        response = requests.post(
            "http://127.0.0.1:5000/api/analyze/detailed",
            json={
                "username": "jay_fh",
                "start_date": "2026-01-31",
                "end_date": "2026-02-14",
                "timezone": timezone,
                "include_mistake_analysis": False,
                "include_ai_advice": False
            },
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        print("\n💡 Make sure Flask server is running: uv run python run.py")
        return False
    
    data = response.json()
    sections = data['sections']
    
    # Track results
    all_passed = True
    
    # 1. Total Games
    print("\n1️⃣  Overall Performance")
    expected_total = 84
    actual_total = data['total_games']
    status = "✓" if actual_total == expected_total else "✗"
    all_passed &= (actual_total == expected_total)
    print(f"   {status} Total Games: {actual_total} (expected: {expected_total})")
    
    # 2. Performance by Color
    print("\n2️⃣  Performance by Color")
    
    white = sections['color_performance']['white']
    white_games = white['total']['wins'] + white['total']['losses'] + white['total']['draws']
    white_win_rate = white['win_rate']
    status = "✓" if white_games == 42 and white_win_rate == 50.0 else "✗"
    all_passed &= (white_games == 42 and white_win_rate == 50.0)
    print(f"   {status} White - Games: {white_games} (expected: 42), Win Rate: {white_win_rate}% (expected: 50.0%)")
    
    black = sections['color_performance']['black']
    black_games = black['total']['wins'] + black['total']['losses'] + black['total']['draws']
    black_win_rate = black['win_rate']
    # Allow for rounding differences (57.1% or 57.14%)
    status = "✓" if black_games == 42 and 57.0 <= black_win_rate <= 57.2 else "✗"
    all_passed &= (black_games == 42 and 57.0 <= black_win_rate <= 57.2)
    print(f"   {status} Black - Games: {black_games} (expected: 42), Win Rate: {black_win_rate}% (expected: 57.1%)")
    
    # 3. Termination - Wins
    print("\n3️⃣  How You Win")
    wins_data = sections['termination_wins']
    wins_total = wins_data['total_wins']
    wins_breakdown = wins_data['breakdown']
    
    expected_wins = {
        'resignation': 25,
        'checkmate': 10,
        'timeout': 9,
        'abandoned': 1
    }
    
    status = "✓" if wins_total == 45 else "✗"
    all_passed &= (wins_total == 45)
    print(f"   {status} Total Wins: {wins_total} (expected: 45)")
    
    for method, expected_count in expected_wins.items():
        actual_count = wins_breakdown.get(method, 0)
        status = "✓" if actual_count == expected_count else "✗"
        all_passed &= (actual_count == expected_count)
        print(f"   {status}   {method}: {actual_count} (expected: {expected_count})")
    
    # 4. Termination - Losses
    print("\n4️⃣  How You Lose")
    losses_data = sections['termination_losses']
    losses_total = losses_data['total_losses']
    losses_breakdown = losses_data['breakdown']
    
    expected_losses = {
        'resignation': 24,
        'timeout': 9,
        'checkmate': 3,
        'abandoned': 2
    }
    
    status = "✓" if losses_total == 38 else "✗"
    all_passed &= (losses_total == 38)
    print(f"   {status} Total Losses: {losses_total} (expected: 38)")
    
    for method, expected_count in expected_losses.items():
        actual_count = losses_breakdown.get(method, 0)
        status = "✓" if actual_count == expected_count else "✗"
        all_passed &= (actual_count == expected_count)
        print(f"   {status}   {method}: {actual_count} (expected: {expected_count})")
    
    # 5. Opponent Strength
    print("\n5️⃣  Opponent Strength Analysis")
    opponent_data = sections['opponent_strength']['by_rating_diff']
    
    similar_games = opponent_data['similar']['games']
    higher_games = opponent_data['higher']['games']
    
    status = "✓" if similar_games == 83 else "✗"
    all_passed &= (similar_games == 83)
    print(f"   {status} Similar Rated: {similar_games} games (expected: 83)")
    
    status = "✓" if higher_games == 1 else "✗"
    all_passed &= (higher_games == 1)
    print(f"   {status} Higher Rated: {higher_games} games (expected: 1)")
    
    # Verify opponent total
    opponent_total = sum(
        opponent_data[cat]['games']
        for cat in ['much_lower', 'lower', 'similar', 'higher', 'much_higher']
    )
    status = "✓" if opponent_total == 84 else "✗"
    all_passed &= (opponent_total == 84)
    print(f"   {status} Total across all categories: {opponent_total} (expected: 84)")
    
    # 6. Time of Day
    print("\n6️⃣  Time of Day Performance")
    time_data = sections['time_of_day']
    
    if not skip_time_check:
        expected_time = {
            'morning': 9,
            'afternoon': 45,
            'evening': 15,
            'night': 15
        }
        
        for period, expected_games in expected_time.items():
            actual_games = time_data[period]['games']
            status = "✓" if actual_games == expected_games else "✗"
            all_passed &= (actual_games == expected_games)
            print(f"   {status} {period.capitalize()}: {actual_games} games (expected: {expected_games})")
    else:
        # Just show the values without validation
        print("   ⚠️  Skipping validation (timezone-dependent)")
        for period in ['morning', 'afternoon', 'evening', 'night']:
            actual_games = time_data[period]['games']
            print(f"   ℹ️  {period.capitalize()}: {actual_games} games")
    
    # Verify time total
    time_total = sum(time_data[period]['games'] for period in ['morning', 'afternoon', 'evening', 'night'])
    status = "✓" if time_total == 84 else "✗"
    all_passed &= (time_total == 84)
    print(f"   {status} Total across all periods: {time_total} (expected: 84)")
    
    # 7. Data Consistency
    print("\n7️⃣  Data Consistency Checks")
    
    # Check wins + losses + draws = total
    white = sections['color_performance']['white']
    black = sections['color_performance']['black']
    total_draws = white['total']['draws'] + black['total']['draws']
    total_results = wins_total + losses_total + total_draws
    status = "✓" if total_results == 84 else "✗"
    all_passed &= (total_results == 84)
    print(f"   {status} Wins + Losses + Draws = {wins_total}W + {losses_total}L + {total_draws}D = {total_results} (expected: 84)")
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All validations PASSED! System is working correctly.")
        return True
    else:
        print("❌ Some validations FAILED. Check output above for details.")
        return False


if __name__ == "__main__":
    import sys
    
    # Default timezone for this test case: Asia/Jakarta (GMT+7)
    # User can specify alternate timezone as first argument
    timezone = sys.argv[1] if len(sys.argv) > 1 else "Asia/Jakarta"
    # Skip time check by default unless explicitly enabled with "false"
    skip_time = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else False
    
    success = verify_test_case(timezone=timezone, skip_time_check=skip_time)
    exit(0 if success else 1)
