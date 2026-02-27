"""Test Stockfish fallback performance with shallow depth."""
import time
import chess
from app.services.mistake_analysis_service import MistakeAnalysisService

def main():
    print("\nTesting Stockfish fallback performance with 100ms time limit\n")
    print("="*70)
    
    # Create service with Lichess enabled
    service = MistakeAnalysisService(
        stockfish_path='stockfish',
        engine_depth=8,  # Full depth (should be overridden for fallback)
        time_limit=0.2,
        enabled=True,
        use_lichess_cloud=True,
        lichess_timeout=5.0
    )
    
    service.engine = service._start_engine()
    if not service.engine:
        print("ERROR: Stockfish engine not available")
        return
    
    # Test position that's NOT in Lichess database
    obscure_fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 5"
    board = chess.Board(obscure_fen)
    
    print("\nTesting 10 Stockfish fallback calls (positions not in Lichess DB)...")
    total_time = 0
    
    for i in range(10):
        start = time.time()
        result = service._evaluate_position(board)
        elapsed = time.time() - start
        total_time += elapsed
        print(f"  Call {i+1}: {elapsed:.3f}s (result: {result} CP)")
    
    avg_time = total_time / 10
    print(f"\nResults:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average per call: {avg_time:.3f}s")
    print(f"  Expected time savings: {17 * avg_time:.2f}s for 17 fallbacks")
    
    service._stop_engine()
    
    # Calculate expected total game analysis time
    lichess_time = 27 * 0.03  # 27 hits at ~0.03s each
    stockfish_time = 17 * avg_time  # 17 misses
    total_expected = lichess_time + stockfish_time
    
    print(f"\nExpected game analysis time:")
    print(f"  Lichess (27 positions): ~{lichess_time:.2f}s")
    print(f"  Stockfish fallback (17 positions): ~{stockfish_time:.2f}s")
    print(f"  Total: ~{total_expected:.2f}s")
    
    if total_expected <= 5:
        print(f"  ✅ Should meet performance target (≤5s)")
    else:
        print(f"  ❌ May not meet performance target (≤5s)")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
