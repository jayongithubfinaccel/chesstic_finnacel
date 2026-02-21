"""
Test the async mistake analysis functionality.
This script tests the end-to-end flow:
1. Submit analysis request
2. Check for 'processing' status in response
3. Poll the status endpoint
4. Verify results are returned when complete
"""
import requests
import json
import time

print("🧪 Testing Async Mistake Analysis...")
print("=" * 70)

# Step 1: Submit analysis request
print("\n📤 Step 1: Submitting analysis request...")
response = requests.post(
    "http://127.0.0.1:5000/api/analyze/detailed",
    json={
        "username": "jay_fh",
        "start_date": "2026-02-10",
        "end_date": "2026-02-17",
        "timezone": "Asia/Jakarta",
        "include_mistake_analysis": True,
        "include_ai_advice": False
    },
    timeout=120
)

if response.status_code != 200:
    print(f"❌ Request failed with status {response.status_code}")
    print(f"Response: {response.text}")
    exit(1)

data = response.json()
print(f"✅ Response received (HTTP {response.status_code})")
print(f"   Total games: {data.get('total_games', 'N/A')}")
print(f"   Sections available: {list(data.get('sections', {}).keys())}")

# Step 2: Check mistake analysis status
mistake_analysis = data.get('sections', {}).get('mistake_analysis', {})
print(f"\n📊 Step 2: Checking mistake analysis status...")
print(f"   Status: {mistake_analysis.get('status', 'N/A')}")

if mistake_analysis.get('status') == 'processing':
    task_id = mistake_analysis.get('task_id')
    estimated_time = mistake_analysis.get('estimated_time')
    message = mistake_analysis.get('message')
    
    print(f"   ✅ Processing in background!")
    print(f"   Task ID: {task_id}")
    print(f"   Estimated time: {estimated_time}")
    print(f"   Message: {message}")
    
    # Step 3: Poll for results
    print(f"\n🔄 Step 3: Polling for results (every 2 seconds)...")
    poll_count = 0
    max_polls = 60  # 2 minutes max
    
    while poll_count < max_polls:
        time.sleep(2)
        poll_count += 1
        
        status_response = requests.get(
            f"http://127.0.0.1:5000/api/analyze/mistake-status/{task_id}",
            timeout=10
        )
        
        if status_response.status_code != 200:
            print(f"   ❌ Poll {poll_count} failed with status {status_response.status_code}")
            continue
        
        status_data = status_response.json()
        current_status = status_data.get('status')
        
        if current_status == 'processing':
            progress = status_data.get('progress', {})
            remaining = status_data.get('estimated_remaining', 'Unknown')
            print(f"   ⏳ Poll {poll_count}: Processing... {progress.get('current')}/{progress.get('total')} ({progress.get('percentage')}%) - {remaining}")
            
        elif current_status == 'completed':
            print(f"   ✅ Poll {poll_count}: Analysis complete!")
            
            # Check the data
            result_data = status_data.get('data', {})
            print(f"\n📈 Step 4: Validating results...")
            print(f"   Weakest stage: {result_data.get('weakest_stage', 'N/A')}")
            print(f"   Total games analyzed: {result_data.get('total_games_analyzed', 'N/A')}")
            
            # Check by_stage data
            by_stage = result_data.get('by_stage', {})
            if by_stage:
                print(f"\n   📊 Breakdown by stage:")
                for stage in ['early', 'middle', 'endgame']:
                    if stage in by_stage:
                        stage_data = by_stage[stage]
                        total_mistakes = (stage_data.get('inaccuracies', 0) + 
                                        stage_data.get('mistakes', 0) + 
                                        stage_data.get('blunders', 0))
                        print(f"      {stage.capitalize()}:")
                        print(f"         Total moves: {stage_data.get('total_moves', 0)}")
                        print(f"         Total mistakes: {total_mistakes}")
                        print(f"         Avg CP loss: {stage_data.get('avg_cp_loss', 0):.1f}")
                
                print(f"\n🎉 Async mistake analysis is working perfectly!")
                print("=" * 70)
            else:
                print(f"   ⚠️ No by_stage data returned")
            
            break
            
        elif current_status == 'error':
            print(f"   ❌ Poll {poll_count}: Analysis failed!")
            print(f"      Error: {status_data.get('error', 'Unknown error')}")
            break
            
        elif current_status == 'not_found':
            print(f"   ❌ Poll {poll_count}: Task not found (may have expired)")
            break
        
        else:
            print(f"   ⚠️ Poll {poll_count}: Unknown status: {current_status}")
            break
    
    if poll_count >= max_polls:
        print(f"\n❌ Polling timed out after {max_polls} attempts")
        
elif mistake_analysis.get('status') == 'completed':
    print(f"   ✅ Analysis already complete (synchronous mode)")
    print(f"   Weakest stage: {mistake_analysis.get('weakest_stage', 'N/A')}")
else:
    print(f"   ⚠️ Unexpected status: {mistake_analysis.get('status', 'N/A')}")

print("=" * 70)
