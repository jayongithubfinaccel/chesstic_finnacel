"""Diagnostic test to check Lichess integration in analyze_game_mistakes."""
import time
from app.services.mistake_analysis_service import MistakeAnalysisService

# Sample PGN for testing
SAMPLE_PGN = """[Event "Live Chess"]
[Site "Chess.com"]
[Date "2026.02.26"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6 5. d3 d6 6. c3 O-O 7. Bb3 a6 
8. Nbd2 Ba7 9. h3 h6 10. Re1 Re8 11. Nf1 Be6 12. Ng3 Bxb3 13. Qxb3 Qd7 
14. Nh2 Rad8 15. Nhf1 Kh7 16. Be3 Bxe3 17. Nxe3 Ne7 18. Nef5 Nxf5 
19. Nxf5 Qe6 20. Qxe6 fxe6 21. Ng3 Nh5 22. Nxh5 1-0
"""

def main():
    print("Diagnostic test for Lichess integration in analyze_game_mistakes\n")
    print("="*70)
    
    # Initialize service with Lichess enabled
    print("\n1. Initializing MistakeAnalysisService with Lichess enabled...")
    service = MistakeAnalysisService(
        stockfish_path='stockfish',
        engine_depth=8,
        time_limit=0.2,
        enabled=True,
        use_lichess_cloud=True,
        lichess_timeout=1.0
    )
    print(f"   use_lichess_cloud: {service.use_lichess_cloud}")
    print(f"   lichess_service: {service.lichess_service}")
    print(f"   enabled: {service.enabled}")
    
    # Start engine
    print("\n2. Starting Stockfish engine...")
    service.engine = service._start_engine()
    if not service.engine:
        print("   ERROR: Stockfish engine not available!")
        return
    print("   Engine started successfully")
    
    try:
        print("\n3. Analyzing game...")
        start_time = time.time()
        result = service.analyze_game_mistakes(SAMPLE_PGN, 'white')
        elapsed = time.time() - start_time
        
        print(f"\n4. Analysis Results:")
        print(f"   Time elapsed: {elapsed:.2f}s")
        print(f"   Early moves: {result['early']['total_moves']}")
        print(f"   Middle moves: {result['middle']['total_moves']}")
        print(f"   Endgame moves: {result['endgame']['total_moves']}")
        
        print(f"\n5. Lichess API Statistics:")
        if service.lichess_service:
            stats = service.lichess_service.get_stats()
            print(f"   API Calls: {stats['api_calls']}")
            print(f"   Hits: {stats['hits']}")
            print(f"   Misses: {stats['misses']}")
            print(f"   Errors: {stats['errors']}")
            print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
            
            if stats['hits'] > 0:
                print(f"\n   ✅ Lichess integration IS working!")
                print(f"   Expected time savings: ~{stats['hits'] * 0.03:.2f}s saved")
            else:
                print(f"\n   ❌ Lichess integration NOT working - no hits!")
        else:
            print("   ERROR: Lichess service not initialized!")
        
        print(f"\n6. Performance Analysis:")
        if elapsed > 10:
            print(f"   ⚠️  Slow performance ({elapsed:.2f}s) suggests Stockfish fallback")
        elif elapsed < 5:
            print(f"   ✅ Fast performance ({elapsed:.2f}s) suggests Lichess is working")
        else:
            print(f"   ⚠️  Moderate performance ({elapsed:.2f}s) - mixed?")
        
    finally:
        print("\n7. Cleaning up...")
        service._stop_engine()
        print("   Engine stopped")
    
    print("\n" + "="*70)
    print("Diagnostic test complete\n")

if __name__ == "__main__":
    main()
