"""
Quick test for Mistake Analysis with Stockfish.
Tests with a small dataset to verify engine is working.
"""
import requests
import json

print("🧪 Testing Mistake Analysis with Stockfish...")
print("=" * 60)

# Test with smaller dataset for faster testing
response = requests.post(
    "http://127.0.0.1:5000/api/analyze/detailed",
    json={
        "username": "jay_fh",
        "start_date": "2026-02-07",  # Smaller range for faster testing
        "end_date": "2026-02-14",
        "timezone": "Asia/Jakarta",
        "include_mistake_analysis": True,
        "include_ai_advice": False
    },
    timeout=300  # 5 minutes timeout for engine analysis
)

if response.status_code == 200:
    data = response.json()
    
    print("✅ API Response received")
    print(f"   Total games: {data['total_games']}")
    
    if 'mistake_analysis' in data['sections']:
        mistake = data['sections']['mistake_analysis']
        
        print("\n📊 Mistake Analysis Results:")
        print(f"   Games analyzed: {mistake.get('total_games_analyzed', 'N/A')}")
        print(f"   Sample percentage: {mistake.get('sample_percentage', 'N/A')}%")
        print(f"   Weakest stage: {mistake.get('weakest_stage', 'N/A')}")
        
        if 'by_stage' in mistake:
            print("\n📈 By Stage:")
            for stage in ['early', 'middle', 'endgame']:
                if stage in mistake['by_stage']:
                    stage_data = mistake['by_stage'][stage]
                    print(f"   {stage.capitalize()}:")
                    print(f"      Total moves: {stage_data.get('total_moves', 0)}")
                    print(f"      Inaccuracies: {stage_data.get('inaccuracies', 0)}")
                    print(f"      Mistakes: {stage_data.get('mistakes', 0)}")
                    print(f"      Blunders: {stage_data.get('blunders', 0)}")
                    print(f"      Avg CP loss: {stage_data.get('avg_cp_loss', 0):.1f}")
        
        print("\n🎉 Mistake Analysis is working!")
    else:
        print("\n❌ No mistake_analysis section in response")
        print("   Available sections:", list(data['sections'].keys()))
else:
    print(f"\n❌ API request failed with status {response.status_code}")
    print(f"   Response: {response.text[:500]}")

print("=" * 60)
