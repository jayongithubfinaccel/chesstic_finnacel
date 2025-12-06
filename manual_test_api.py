"""
Manual test script for testing the detailed analytics endpoint with real Chess.com data.

Usage:
    uv run python manual_test_api.py
"""
import requests
import json
from datetime import datetime, timedelta


def test_analyze_detailed_api():
    """Test the /api/analyze/detailed endpoint with real user data."""
    
    # API endpoint (adjust if your server runs on different port)
    base_url = "http://localhost:5000"
    endpoint = f"{base_url}/api/analyze/detailed"
    
    # Test user (from PRD)
    username = "jay_fh"
    
    # Date range (last 3 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # Request payload
    payload = {
        "username": username,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "timezone": "America/New_York"
    }
    
    print(f"Testing endpoint: {endpoint}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n" + "="*60 + "\n")
    
    try:
        # Make request
        print("Sending request...")
        response = requests.post(endpoint, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f} seconds")
        print("\n" + "="*60 + "\n")
        
        # Parse response
        if response.status_code == 200:
            data = response.json()
            
            print("✅ SUCCESS!\n")
            print(f"Username: {data.get('username')}")
            print(f"Date Range: {data.get('start_date')} to {data.get('end_date')}")
            print(f"Timezone: {data.get('timezone')}")
            print(f"Total Games: {data.get('total_games')}")
            print("\n" + "-"*60 + "\n")
            
            sections = data.get('sections', {})
            
            # Overall Performance
            overall = sections.get('overall_performance', {})
            daily_stats = overall.get('daily_stats', [])
            print(f"📊 Overall Performance: {len(daily_stats)} days with games")
            
            # Color Performance
            color_perf = sections.get('color_performance', {})
            white_wr = color_perf.get('white', {}).get('win_rate', 0)
            black_wr = color_perf.get('black', {}).get('win_rate', 0)
            print(f"⚪ White Win Rate: {white_wr}%")
            print(f"⚫ Black Win Rate: {black_wr}%")
            
            # Elo Progression
            elo = sections.get('elo_progression', {})
            rating_change = elo.get('rating_change', 0)
            print(f"📈 Rating Change: {rating_change:+d}")
            
            # Termination Analysis
            term_wins = sections.get('termination_wins', {})
            term_losses = sections.get('termination_losses', {})
            print(f"🏆 Win Methods: {len(term_wins)} types")
            print(f"😔 Loss Methods: {len(term_losses)} types")
            
            # Opening Performance
            openings = sections.get('opening_performance', {})
            best = openings.get('best_openings', [])
            worst = openings.get('worst_openings', [])
            print(f"♟️  Best Openings: {len(best)}")
            print(f"♟️  Worst Openings: {len(worst)}")
            
            if best:
                print(f"   Top Opening: {best[0].get('name')} ({best[0].get('win_rate')}% in {best[0].get('games')} games)")
            
            # Opponent Strength
            opp_str = sections.get('opponent_strength', {})
            lower = opp_str.get('lower_rated', {})
            similar = opp_str.get('similar_rated', {})
            higher = opp_str.get('higher_rated', {})
            print(f"💪 vs Lower: {lower.get('win_rate')}% ({lower.get('games')} games)")
            print(f"⚖️  vs Similar: {similar.get('win_rate')}% ({similar.get('games')} games)")
            print(f"🔥 vs Higher: {higher.get('win_rate')}% ({higher.get('games')} games)")
            
            # Time of Day
            tod = sections.get('time_of_day', {})
            morning = tod.get('morning', {})
            afternoon = tod.get('afternoon', {})
            night = tod.get('night', {})
            print(f"🌅 Morning: {morning.get('win_rate')}% ({morning.get('games')} games)")
            print(f"☀️  Afternoon: {afternoon.get('win_rate')}% ({afternoon.get('games')} games)")
            print(f"🌙 Night: {night.get('win_rate')}% ({night.get('games')} games)")
            
            print("\n" + "="*60 + "\n")
            print("✅ All 8 analytics sections processed successfully!")
            
            # Performance check
            elapsed = response.elapsed.total_seconds()
            if elapsed < 6:
                print(f"✅ Performance OK: {elapsed:.2f}s (target: < 6s)")
            else:
                print(f"⚠️  Performance Warning: {elapsed:.2f}s (target: < 6s)")
        
        else:
            print("❌ ERROR!\n")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error')}")
                print(f"Status: {error_data.get('status')}")
                if 'details' in error_data:
                    print(f"Details: {error_data.get('details')}")
            except:
                print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("Make sure the Flask server is running:")
        print("  uv run python run.py")
    except requests.exceptions.Timeout:
        print("❌ Request Timeout!")
        print("The request took too long. Try a shorter date range.")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


if __name__ == "__main__":
    test_analyze_detailed_api()
