"""
Debug script to see actual API response structure.
"""
import requests
import json

response = requests.post(
    "http://127.0.0.1:5000/api/analyze/detailed",
    json={
        "username": "jay_fh",
        "start_date": "2026-01-31",
        "end_date": "2026-02-14",
        "timezone": "Asia/Jakarta",
        "include_mistake_analysis": False,
        "include_ai_advice": False
    },
    timeout=30
)

data = response.json()

print("=" * 60)
print("TERMINATION WINS BREAKDOWN:")
print(json.dumps(data['sections']['termination_wins']['breakdown'], indent=2))

print("\n" + "=" * 60)
print("TERMINATION LOSSES BREAKDOWN:")
print(json.dumps(data['sections']['termination_losses']['breakdown'], indent=2))

print("\n" + "=" * 60)
print("TIME OF DAY:")
for period in ['morning', 'afternoon', 'evening', 'night']:
    games = data['sections']['time_of_day'][period]['games']
    print(f"{period.capitalize()}: {games} games")

print("\n" + "=" * 60)
print("COLOR PERFORMANCE:")
white = data['sections']['color_performance']['white']
black = data['sections']['color_performance']['black']
print(f"White win rate: {white['win_rate']}%")
print(f"Black win rate: {black['win_rate']}%")
print(f"White draws: {white['total']['draws']}")
print(f"Black draws: {black['total']['draws']}")
