"""
Debug test for analytics service issues.
Run this to identify which sections are failing.
"""
import sys
import json
from datetime import datetime

from app.services.chess_service import ChessService
from app.services.analytics_service import AnalyticsService

# Configuration
USERNAME = 'jay_fh'
START_DATE = '2026-01-31'
END_DATE = '2026-02-14'
TIMEZONE = 'America/New_York'

print("="*60)
print("ANALYTICS DEBUG TEST")
print("="*60)
print(f"Username: {USERNAME}")
print(f"Date Range: {START_DATE} to {END_DATE}")
print(f"Timezone: {TIMEZONE}")
print()

# Step 1: Fetch games
print("Step 1: Fetching games...")
chess_service = ChessService()
try:
    result = chess_service.analyze_games(USERNAME, START_DATE, END_DATE)
    games = result.get('games', [])
    print(f"✓ Fetched {len(games)} games")
except Exception as e:
    print(f"✗ Error fetching games: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if not games:
    print("No games to analyze. Exiting.")
    sys.exit(0)

print(f"\nSample game data:")
sample = games[0]
print(f"  - White: {sample.get('white', {}).get('username', 'N/A')}")
print(f"  - Black: {sample.get('black', {}).get('username', 'N/A')}")
print(f"  - White result: {sample.get('white', {}).get('result', 'N/A')}")
print(f"  - Black result: {sample.get('black', {}).get('result', 'N/A')}")
print(f"  - Has PGN: {bool(sample.get('pgn', ''))}")

# Step 2: Initialize analytics service
print("\n" + "="*60)
print("Step 2: Initializing analytics service...")
analytics_service = AnalyticsService(
    stockfish_path='stockfish',
    engine_depth=12,
    engine_enabled=True,
    openai_api_key='',
    openai_model='gpt-4o-mini'
)
print("✓ Analytics service initialized")

# Step 3: Test individual analysis functions
print("\n" + "="*60)
print("Step 3: Testing individual analysis functions...")

# Parse and enrich games first
print("\n3.1: Parsing and enriching games...")
try:
    enriched_games = analytics_service._parse_and_enrich_games(games, USERNAME, TIMEZONE)
    print(f"✓ Enriched {len(enriched_games)} games")
    
    # Show sample enriched game
    if enriched_games:
        sample_enriched = enriched_games[0]
        print(f"\nSample enriched game:")
        print(f"  - Player color: {sample_enriched.get('player_color')}")
        print(f"  - Result: {sample_enriched.get('result')}")
        print(f"  - Termination: {sample_enriched.get('termination')}")
        print(f"  - Opening: {sample_enriched.get('opening_name')}")
        print(f"  - Time of day: {sample_enriched.get('time_of_day')}")
except Exception as e:
    print(f"✗ Error enriching games: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test each analysis section
sections_to_test = [
    ('overall_performance', '_analyze_overall_performance'),
    ('color_performance', '_analyze_color_performance'),
    ('elo_progression', '_analyze_elo_progression'),
    ('termination_wins', '_analyze_termination_wins'),
    ('termination_losses', '_analyze_termination_losses'),
    ('opening_performance', '_analyze_opening_performance'),
    ('opponent_strength', '_analyze_opponent_strength'),
    ('time_of_day', '_analyze_time_of_day'),
]

results = {}
for section_name, method_name in sections_to_test:
    print(f"\n3.{len(results)+2}: Testing {section_name}...")
    try:
        method = getattr(analytics_service, method_name)
        result = method(enriched_games)
        results[section_name] = result
        
        # Display key metrics
        if section_name == 'termination_wins':
            print(f"  Total wins: {result.get('total_wins', 0)}")
            print(f"  Breakdown: {result.get('breakdown', {})}")
        elif section_name == 'termination_losses':
            print(f"  Total losses: {result.get('total_losses', 0)}")
            print(f"  Breakdown: {result.get('breakdown', {})}")
        elif section_name == 'opening_performance':
            white_best = result.get('white', {}).get('best_openings', [])
            black_best = result.get('black', {}).get('best_openings', [])
            print(f"  White best openings: {len(white_best)}")
            print(f"  Black best openings: {len(black_best)}")
            if white_best:
                print(f"    Top: {white_best[0].get('opening', 'N/A')} ({white_best[0].get('games', 0)} games)")
        elif section_name == 'opponent_strength':
            by_diff = result.get('by_rating_diff', {})
            total_games = sum(cat.get('games', 0) for cat in by_diff.values())
            print(f"  Total games categorized: {total_games}")
            for cat, data in by_diff.items():
                if data.get('games', 0) > 0:
                    print(f"    {cat}: {data.get('games', 0)} games")
        elif section_name == 'time_of_day':
            total_games = sum(period.get('games', 0) for period in result.values())
            print(f"  Total games categorized: {total_games}")
            for period, data in result.items():
                if data.get('games', 0) > 0:
                    print(f"    {period}: {data.get('games', 0)} games")
        
        print(f"  ✓ {section_name} completed successfully")
    except Exception as e:
        print(f"  ✗ ERROR in {section_name}: {e}")
        import traceback
        traceback.print_exc()
        results[section_name] = None

# Step 4: Validate totals
print("\n" + "="*60)
print("Step 4: Validating data consistency...")

# Count results manually
win_count = sum(1 for g in enriched_games if g['result'] == 'win')
loss_count = sum(1 for g in enriched_games if g['result'] == 'loss')
draw_count = sum(1 for g in enriched_games if g['result'] == 'draw')

print(f"\nExpected counts from enriched games:")
print(f"  Wins: {win_count}")
print(f"  Losses: {loss_count}")
print(f"  Draws: {draw_count}")
print(f"  Total: {len(enriched_games)}")

# Check termination sections
if results.get('termination_wins'):
    actual_wins = results['termination_wins'].get('total_wins', 0)
    print(f"\nTermination Wins section:")
    print(f"  Reported: {actual_wins}")
    print(f"  Match: {'✓' if actual_wins == win_count else '✗ MISMATCH'}")

if results.get('termination_losses'):
    actual_losses = results['termination_losses'].get('total_losses', 0)
    print(f"\nTermination Losses section:")
    print(f"  Reported: {actual_losses}")
    print(f"  Match: {'✓' if actual_losses == loss_count else '✗ MISMATCH'}")

# Check time of day totals
if results.get('time_of_day'):
    tod_total = sum(period.get('games', 0) for period in results['time_of_day'].values())
    print(f"\nTime of Day section:")
    print(f"  Reported: {tod_total}")
    print(f"  Match: {'✓' if tod_total == len(enriched_games) else '✗ MISMATCH'}")

# Step 5: Full analysis test
print("\n" + "="*60)
print("Step 5: Testing full analysis_detailed...")
try:
    full_analysis = analytics_service.analyze_detailed(
        games=games,
        username=USERNAME,
        timezone=TIMEZONE,
        include_mistake_analysis=False,  # Skip for speed
        include_ai_advice=False,
        date_range=f"{START_DATE} to {END_DATE}"
    )
    print(f"✓ Full analysis completed")
    print(f"  Total games: {full_analysis.get('total_games', 0)}")
    print(f"  Sections: {list(full_analysis.get('sections', {}).keys())}")
except Exception as e:
    print(f"✗ ERROR in full analysis: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
