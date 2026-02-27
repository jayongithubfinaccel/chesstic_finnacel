"""Quick test to verify mistake analysis is working with Lichess integration."""
import os
os.environ['USE_LICHESS_CLOUD'] = 'true'
os.environ['LICHESS_API_TIMEOUT'] = '1.0'
os.environ['STOCKFISH_PATH'] = 'C:\\stockfish\\stockfish-windows-x86-64-avx2.exe'

from app.services.mistake_analysis_service import MistakeAnalysisService

# Sample PGN
SAMPLE_PGN = """[Event "Live Chess"]
[Site "Chess.com"]
[Date "2026.02.26"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6 5. d3 d6 1-0
"""

def main():
    print("\n" + "="*70)
    print("Testing Mistake Analysis with Lichess Cloud API")
    print("="*70)
    
    # Initialize service
    print("\n1. Initializing MistakeAnalysisService...")
    service = MistakeAnalysisService(
        stockfish_path='C:\\stockfish\\stockfish-windows-x86-64-avx2.exe',
        engine_depth=8,
        time_limit=0.2,
        enabled=True,
        use_lichess_cloud=True,
        lichess_timeout=1.0
    )
    print(f"   ✓ Service initialized")
    print(f"   - use_lichess_cloud: {service.use_lichess_cloud}")
    print(f"   - lichess_service: {service.lichess_service is not None}")
    print(f"   - enabled: {service.enabled}")
    
    # Start engine
    print("\n2. Starting Stockfish engine...")
    service.engine = service._start_engine()
    if not service.engine:
        print("   ✗ ERROR: Stockfish engine not available!")
        return
    print("   ✓ Engine started successfully")
    
    try:
        # Analyze game
        print("\n3. Analyzing sample game (10 moves)...")
        import time
        start_time = time.time()
        
        result = service.analyze_game_mistakes(SAMPLE_PGN, 'white')
        
        elapsed = time.time() - start_time
        
        print(f"\n4. Analysis Results:")
        print(f"   Time elapsed: {elapsed:.2f}s")
        print(f"   Early moves: {result['early']['total_moves']}")
        print(f"   Middle moves: {result['middle']['total_moves']}")
        print(f"   Endgame moves: {result['endgame']['total_moves']}")
        
        if service.lichess_service:
            stats = service.lichess_service.get_stats()
            print(f"\n5. Lichess API Statistics:")
            print(f"   API Calls: {stats['api_calls']}")
            print(f"   Hits: {stats['hits']}")
            print(f"   Misses: {stats['misses']}")
            print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
            
            if stats['hits'] > 0:
                print(f"\n   ✓ Lichess integration IS working!")
            else:
                print(f"\n   ⚠ Lichess integration may not be working")
        
        print(f"\n6. Conclusion:")
        if result['early']['total_moves'] > 0 or result['middle']['total_moves'] > 0:
            print("   ✓ Mistake analysis is WORKING correctly!")
        else:
            print("   ✗ Mistake analysis returned no results")
        
    except Exception as e:
        print(f"\n   ✗ ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n7. Cleaning up...")
        service._stop_engine()
        print("   ✓ Engine stopped")
    
    print("\n" + "="*70)
    print("Test Complete")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
