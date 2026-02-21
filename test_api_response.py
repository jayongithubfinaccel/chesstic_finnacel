"""
Test API endpoint to see actual JSON response structure.
"""
import requests
import json

url = "http://127.0.0.1:5000/api/analyze/detailed"
payload = {
    "username": "jay_fh",
    "start_date": "2026-02-07",
    "end_date": "2026-02-14",
    "timezone": "America/New_York",
    "include_mistake_analysis": False,
    "include_ai_advice": False
}

print("Testing API endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\n" + "="*60)

response = requests.post(url, json=payload)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResponse structure:")
    print(f"  - total_games: {data.get('total_games')}")
    print(f"  - sections keys: {list(data.get('sections', {}).keys())}")
    
    # Check termination sections
    print(f"\n  Termination Wins:")
    tw = data['sections']['termination_wins']
    print(f"    Structure: {tw}")
    
    print(f"\n  Termination Losses:")
    tl = data['sections']['termination_losses']
    print(f"    Structure: {tl}")
    
    print(f"\n  Opening Performance:")
    op = data['sections']['opening_performance']
    print(f"    Keys: {list(op.keys())}")
    if 'white' in op:
        print(f"    White best_openings count: {len(op['white'].get('best_openings', []))}")
        if op['white'].get('best_openings'):
            print(f"    Sample opening: {op['white']['best_openings'][0]}")
    
    print(f"\n  Opponent Strength:")
    os_data = data['sections']['opponent_strength']
    print(f"    Keys: {list(os_data.keys())}")
    if 'by_rating_diff' in os_data:
        print(f"    Categories: {list(os_data['by_rating_diff'].keys())}")
    
    print(f"\n  Time of Day:")
    tod = data['sections']['time_of_day']
    print(f"    Keys: {list(tod.keys())}")
    for period, pdata in tod.items():
        if pdata.get('games', 0) > 0:
            print(f"    {period}: {pdata['games']} games")
    
    print("\n✓ All data looks correct!")
else:
    print(f"Error: {response.text}")
